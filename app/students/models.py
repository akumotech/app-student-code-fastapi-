from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint
from typing import Optional, List
from datetime import date, datetime
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
    demo_signups: List["DemoSignup"] = Relationship(back_populates="student")
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
    demo_date: Optional[date] = None
    status: Optional[str] = Field(default="confirmed")
    student: Optional["Student"] = Relationship(back_populates="demos")
    demo_signups: List["DemoSignup"] = Relationship(back_populates="demo")


class DemoSession(SQLModel, table=True):
    """Weekly Friday Demo Sessions"""
    __tablename__ = "demo_session"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_date: date = Field(index=True)  # The Friday date
    
    # Session configuration
    is_active: bool = Field(default=True)  # Can students sign up?
    is_cancelled: bool = Field(default=False)  # Is this session cancelled?
    max_scheduled: Optional[int] = Field(default=None)  # Optional limit on signups
    
    # Metadata
    title: Optional[str] = Field(default="Friday Demo Session")
    description: Optional[str] = None
    notes: Optional[str] = None  # Admin notes about the session
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    signups: List["DemoSignup"] = Relationship(back_populates="session")


class DemoSignup(SQLModel, table=True):
    """Student signup for a specific demo session"""
    __tablename__ = "demo_signup"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="demo_session.id")
    student_id: int = Field(foreign_key="student.id")
    demo_id: Optional[int] = Field(default=None, foreign_key="demo.id")
    
    # Status tracking
    status: str = Field(default="scheduled")  # scheduled, presented, no_show, cancelled
    signup_notes: Optional[str] = None  # Student's notes about their demo
    
    # Presentation tracking (admin filled)
    did_present: Optional[bool] = Field(default=None)
    presentation_notes: Optional[str] = None  # Admin notes after presentation
    presentation_rating: Optional[int] = Field(default=None)  # 1-5 rating by admin
    
    # Timestamps
    scheduled_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    session: "DemoSession" = Relationship(back_populates="signups")
    student: "Student" = Relationship(back_populates="demo_signups")
    demo: Optional["Demo"] = Relationship(back_populates="demo_signups")
    
    # Ensure a student can only sign up once per session
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="unique_student_session"),)
