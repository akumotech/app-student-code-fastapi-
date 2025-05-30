from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session  # Changed from sqlalchemy.orm to sqlmodel
from typing import Any  # For APIResponse data

from app.auth import crud as auth_crud  # Renamed to avoid conflict with any local crud
from app.auth.database import get_session
from app.auth.utils import get_current_active_user
from app.auth.schemas import (
    User as UserSchema,
)  # For current_user type hint and response
from app.auth.models import User  # For type hinting target_user

from .schemas import UserRoleUpdate  # Import from local admin schemas
from app.core.schemas import APIResponse  # Import from core schemas

# Define a standard API response model - can be shared or defined locally
# class APIResponse(BaseModel):
#     success: bool
#     message: str | None = None
#     data: Any | None = None
#     error: str | None = None


router = APIRouter(
    tags=["Admin"],  # Tag for OpenAPI docs
)

VALID_ROLES = ["student", "instructor", "admin", "user"]


def require_admin_role(current_user: UserSchema = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action.",
        )
    return current_user


@router.put(
    "/users/{user_id}/role",
    response_model=APIResponse,
    summary="Admin: Update User Role",
    dependencies=[Depends(require_admin_role)],
)
async def admin_update_user_role(
    user_id: int, role_update: UserRoleUpdate, db: Session = Depends(get_session)
):
    if role_update.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}",
        )

    target_user: User | None = auth_crud.get_user_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )

    target_user.role = role_update.role
    db.add(target_user)
    try:
        db.commit()
        db.refresh(target_user)
    except Exception as e:
        db.rollback()
        # Log error e
        # print(f"Error updating user role: {e}") # Basic logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role.",
        )

    return APIResponse(
        success=True,
        message=f"User {user_id}'s role updated to {role_update.role}.",
        data=UserSchema.from_orm(target_user),
    )
