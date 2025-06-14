from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from pydantic import EmailStr
from app.students.models import BatchInstructorLink, BatchStudentLink


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, sa_column_kwargs={"unique": True})
    name: str
    disabled: Optional[bool] = Field(default=False)
    password: str
    wakatime_access_token_encrypted: Optional[str] = None
    wakatime_refresh_token_encrypted: Optional[str] = None
    role: Optional[str] = Field(
        default="none"
    )  # 'student', 'instructor', 'admin', 'none'

    daily_summaries: List["DailySummary"] = Relationship(back_populates="user")
    instructor_batches: List["Batch"] = Relationship(
        back_populates="instructors", link_model=BatchInstructorLink
    )
    student_batches: List["Batch"] = Relationship(
        back_populates="student_users", link_model=BatchStudentLink
    )
