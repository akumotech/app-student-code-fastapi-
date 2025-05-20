from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date

class Student(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    batch: str
    project: str
    certificates: List["Certificate"] = Relationship(back_populates="student")
    demos: List["Demo"] = Relationship(back_populates="student")
    # Add more student-specific fields as needed

class Certificate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    name: str
    issuer: Optional[str] = None
    date_issued: Optional[date]
    date_expired: Optional[date]
    description: Optional[str] = None
    student: Optional["Student"] = Relationship(back_populates="certificates")

class Demo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    title: str
    description: Optional[str] = None
    link: Optional[str] = None
    date: Optional[date]
    status: Optional[str] = Field(default="confirmed") ## (confirmed, cancelled, done)
    student: Optional["Student"] = Relationship(back_populates="demos")