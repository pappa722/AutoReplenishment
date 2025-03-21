from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    获取用户列表，仅超级管理员可访问
    """
    users = UserService.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取当前登录用户信息
    """
    return current_user


@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    更新当前登录用户信息
    """
    # 防止普通用户自行升级为管理员
    if user_in.is_superuser is not None and user_in.is_superuser != current_user.is_superuser:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，无法修改管理员状态"
            )
    
    user = UserService.update_user(db, user_id=current_user.id, user_in=user_in)
    return user


@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    根据ID获取用户信息
    """
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 普通用户只能查看自己的信息
    if not current_user.is_superuser and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，无法查看其他用户信息"
        )
    
    return user


@router.post("/", response_model=UserSchema)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    创建新用户，仅超级管理员可访问
    """
    # 检查用户名是否已存在
    user = UserService.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if user_in.email:
        user = UserService.get_user_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 创建用户
    user = UserService.create_user(db, user_in=user_in)
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    更新用户信息，仅超级管理员可访问
    """
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user = UserService.update_user(db, user_id=user_id, user_in=user_in)
    return user


@router.delete("/{user_id}", response_model=UserSchema)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    删除用户，仅超级管理员可访问
    """
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法删除当前登录用户"
        )
    
    user = UserService.delete_user(db, user_id=user_id)
    return user


@router.patch("/{user_id}/activate", response_model=UserSchema)
def activate_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    激活用户，仅超级管理员可访问
    """
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user = UserService.activate_user(db, user_id=user_id)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserSchema)
def deactivate_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    停用用户，仅超级管理员可访问
    """
    user = UserService.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止停用自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法停用当前登录用户"
        )
    
    user = UserService.deactivate_user(db, user_id=user_id)
    return user