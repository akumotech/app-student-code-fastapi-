from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from pydantic import EmailStr


class AdminActivityLog(SQLModel, table=True):
    """Track admin activities for audit purposes"""
    __tablename__ = "admin_activity_log"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    admin_user_id: int = Field(foreign_key="user.id")
    action: str  # "role_update", "student_update", "user_disable", etc.
    target_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    target_student_id: Optional[int] = Field(default=None, foreign_key="student.id")
    details: Optional[str] = None  # JSON string with action details
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UserSession(SQLModel, table=True):
    """Track user login sessions"""
    __tablename__ = "user_session"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    session_token: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = Field(default=True)
