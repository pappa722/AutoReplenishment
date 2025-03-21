from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.token import TokenPayload
from app.services.user_service import UserService

# 定义OAuth2密码流，指定令牌URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_db() -> Generator:
    """
    获取数据库会话依赖
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前用户依赖
    
    Args:
        db: 数据库会话
        token: JWT令牌
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 如果令牌无效或用户不存在
    """
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库获取用户
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查用户是否已被禁用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户依赖
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前活跃用户对象
        
    Raises:
        HTTPException: 如果用户已被禁用
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃超级管理员依赖
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前活跃超级管理员对象
        
    Raises:
        HTTPException: 如果用户不是超级管理员
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要超级管理员权限"
        )
    return current_user