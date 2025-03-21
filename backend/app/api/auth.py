from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.schemas.user import UserCreate, User
from app.schemas.token import Token

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 兼容的令牌登录，获取访问令牌
    """
    user = AuthService.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": AuthService.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=User)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    """
    注册新用户
    """
    # 检查用户名是否已存在
    user = UserService.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    user = UserService.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )
    
    # 创建新用户，普通注册用户不允许设置超级管理员权限
    user_data = user_in.dict()
    user_data["is_superuser"] = False
    
    user = UserService.create_user(db, UserCreate(**user_data))
    
    return user


@router.post("/test-token", response_model=User)
def test_token(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    测试访问令牌
    """
    return current_user


@router.post("/refresh-token", response_model=Token)
def refresh_token(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    刷新访问令牌
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": AuthService.create_access_token(
            current_user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }