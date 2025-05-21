from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date

class BatchInstructorLink(SQLModel, table=True):
    batch_id: int = Field(foreign_key="batches.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)

class BatchStudentLink(SQLModel, table=True):
    batch_id: int = Field(foreign_key="batches.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)

class Batches(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    start_date: date
    end_date: date
    slack_channel: str
    curriculum: Optional[str] = None  # For simplicity, can be a comma-separated string or JSON
    instructors: List["User"] = Relationship(back_populates="instructor_batches", link_model=BatchInstructorLink)
    students: List["User"] = Relationship(back_populates="student_batches", link_model=BatchStudentLink)
    projects: List["Projects"] = Relationship(back_populates="batches")

class Projects(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    start_date: date
    end_date: date
    happy_hour: Optional[str] = None
    batch_id: int = Field(foreign_key="batches.id")
    batch: Optional[Batches] = Relationship(back_populates="projects")

class Students(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    batch_id: int = Field(foreign_key="batches.id")
    project_id: int = Field(foreign_key="projects.id")
    certificates: List["Certificates"] = Relationship(back_populates="students")
    demos: List["Demos"] = Relationship(back_populates="students")
    # Add more student-specific fields as needed

class Certificates(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    name: str
    issuer: Optional[str] = None
    date_issued: Optional[date] = None
    date_expired: Optional[date] = None
    description: Optional[str] = None
    student: Optional["Students"] = Relationship(back_populates="certificates")

class Demos(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    title: str
    description: Optional[str] = None
    link: Optional[str] = None
    demo_date: Optional[date] = None
    student: Optional["Students"] = Relationship(back_populates="demos")