from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from app.auth.utils import get_current_active_user
from app.auth.schemas import User as UserSchema
from app.auth.database import get_session
from app.students.models import Student
from app.students.crud import get_student_by_user_id_efficient
from app.core.logging import get_logger
from typing import List

logger = get_logger("dependencies")


def get_current_student(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
) -> Student:
    """Get the current user's student profile"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this resource"
        )
    
    student = get_student_by_user_id_efficient(session, current_user.id)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    return student


def get_current_admin_or_instructor(
    current_user: UserSchema = Depends(get_current_active_user),
) -> UserSchema:
    """Ensure current user is admin or instructor"""
    if current_user.role not in ["admin", "instructor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or instructor access required"
        )
    return current_user


def get_current_admin_user(
    current_user: UserSchema = Depends(get_current_active_user),
) -> UserSchema:
    """Ensure current user is admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def validate_student_access(
    student_id: int,
    current_user: UserSchema = Depends(get_current_active_user),
    session: Session = Depends(get_session),
) -> Student:
    """Validate that current user can access the specified student"""
    # Admin and instructors can access any student
    if current_user.role in ["admin", "instructor"]:
        student = session.get(Student, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        return student
    
    # Students can only access their own profile
    if current_user.role == "student":
        student = get_student_by_user_id_efficient(session, current_user.id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found"
            )
        
        if student.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own profile"
            )
        return student
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied"
    )


def require_roles(allowed_roles: List[str]):
    """Decorator to require specific roles"""
    def dependency(
        current_user: UserSchema = Depends(get_current_active_user),
    ) -> UserSchema:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return dependency


# Pre-defined role dependencies
StudentRole = Depends(require_roles(["student"]))
InstructorRole = Depends(require_roles(["instructor"]))
AdminRole = Depends(require_roles(["admin"]))
AdminOrInstructorRole = Depends(require_roles(["admin", "instructor"]))
AnyAuthenticatedRole = Depends(require_roles(["admin", "instructor", "student"])) 