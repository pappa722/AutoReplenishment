from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserInDB, TokenData

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# OAuth2 密码Bearer流
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class AuthService:
    """
    认证服务类：处理用户认证、密码验证和令牌生成
    """
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户凭据
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            如果验证成功返回用户对象，否则返回None
        """
        user = db.query(User).filter(User.username == username).first()
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        创建访问令牌
        
        Args:
            subject: 令牌主题（通常是用户ID）
            expires_delta: 令牌过期时间增量
            
        Returns:
            编码后的JWT令牌
        """
        to_encode = {"sub": str(subject)}
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def get_current_user(
        db: Session = Depends(get_db),
        token: str = Depends(oauth2_scheme)
    ) -> User:
        """
        获取当前用户
        
        Args:
            db: 数据库会话
            token: JWT令牌
            
        Returns:
            当前用户对象
            
        Raises:
            HTTPException: 如果令牌无效或用户不存在
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
            
        user = db.query(User).filter(User.username == token_data.username).first()
        if user is None:
            raise credentials_exception
        return user
    
    @staticmethod
    def get_current_active_user(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        获取当前活跃用户
        
        Args:
            current_user: 当前用户对象
            
        Returns:
            当前活跃用户对象
            
        Raises:
            HTTPException: 如果用户已被禁用
        """
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        return current_user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            如果验证成功，返回用户对象；否则返回None
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user