from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import AuthService

class UserService:
    """
    用户服务类：处理用户相关的业务逻辑
    """
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        通过用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户对象，如果不存在则返回None
        """
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            db: 数据库会话
            email: 电子邮箱
            
        Returns:
            用户对象，如果不存在则返回None
        """
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """
        获取用户列表
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            is_active: 用户状态筛选
            
        Returns:
            用户对象列表
        """
        query = db.query(User)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """
        创建新用户
        
        Args:
            db: 数据库会话
            user: 用户创建模型
            
        Returns:
            新创建的用户对象
            
        Raises:
            HTTPException: 如果用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        if UserService.get_user_by_username(db, username=user.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if UserService.get_user_by_email(db, email=user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 创建新用户对象
        hashed_password = AuthService.get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password,
            full_name=user.full_name,
            is_active=True,
            is_superuser=user.is_superuser
        )
        
        # 保存到数据库
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def update_user(
        db: Session,
        current_user: User,
        user_id: int,
        user_update: UserUpdate
    ) -> User:
        """
        更新用户信息
        
        Args:
            db: 数据库会话
            current_user: 当前操作的用户对象
            user_id: 要更新的用户ID
            user_update: 用户更新模型
            
        Returns:
            更新后的用户对象
            
        Raises:
            HTTPException: 如果用户不存在或无权限
        """
        # 检查要更新的用户是否存在
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查权限
        if not current_user.is_superuser and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # 更新用户信息
        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = AuthService.get_password_hash(
                update_data.pop("password")
            )
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def delete_user(
        db: Session,
        current_user: User,
        user_id: int
    ) -> User:
        """
        删除用户
        
        Args:
            db: 数据库会话
            current_user: 当前操作的用户对象
            user_id: 要删除的用户ID
            
        Returns:
            被删除的用户对象
            
        Raises:
            HTTPException: 如果用户不存在或无权限
        """
        # 检查要删除的用户是否存在
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限执行此操作"
            )
        
        # 软删除用户（将is_active设置为False）
        db_user.is_active = False
        db.commit()
        db.refresh(db_user)
        
        return db_user