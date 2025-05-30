from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date
import uuid


class BatchInstructorLink(SQLModel, table=True):
    batch_id: int = Field(foreign_key="batch.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)


class BatchStudentLink(SQLModel, table=True):
    batch_id: int = Field(foreign_key="batch.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)


class Batch(SQLModel, table=True):
    __tablename__ = "batch"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    registration_key: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
        unique=True,
        index=True,
        nullable=False,
    )
    registration_key_active: bool = Field(default=True)

    slack_channel: str
    curriculum: Optional[str] = (
        None  # For simplicity, can be a comma-separated string or JSON
    )
    instructors: List["User"] = Relationship(
        back_populates="instructor_batches", link_model=BatchInstructorLink
    )
    students: List["Student"] = Relationship(back_populates="batch")
    student_users: List["User"] = Relationship(
        back_populates="student_batches", link_model=BatchStudentLink
    )
    projects: List["Project"] = Relationship(back_populates="batch")


class Project(SQLModel, table=True):
    __tablename__ = "project"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    start_date: date
    end_date: date
    happy_hour: Optional[str] = None
    batch_id: int = Field(foreign_key="batch.id")
    batch: Optional["Batch"] = Relationship(back_populates="projects")
    students: List["Student"] = Relationship(back_populates="project")


class Student(SQLModel, table=True):
    __tablename__ = "student"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)

    batch_id: int = Field(foreign_key="batch.id")
    batch: "Batch" = Relationship(back_populates="students")

    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
    project: Optional["Project"] = Relationship(back_populates="students")

    certificates: List["Certificate"] = Relationship(back_populates="student")
    demos: List["Demo"] = Relationship(back_populates="student")
    # Add more student-specific fields as needed


class Certificate(SQLModel, table=True):
    __tablename__ = "certificate"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    name: str
    issuer: Optional[str] = None
    date_issued: Optional[date] = None
    date_expired: Optional[date] = None
    description: Optional[str] = None
    student: Optional["Student"] = Relationship(back_populates="certificates")


class Demo(SQLModel, table=True):
    __tablename__ = "demo"
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.id")
    title: str
    description: Optional[str] = None
    link: Optional[str] = None
    demo_date: Optional[date] = None
    status: Optional[str] = Field(default="confirmed")
    student: Optional["Student"] = Relationship(back_populates="demos")
