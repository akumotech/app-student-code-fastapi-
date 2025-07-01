from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from pydantic import Field


class BatchInstructorLinkBase(BaseModel):
    batch_id: int
    user_id: int


class BatchStudentLinkBase(BaseModel):
    batch_id: int
    user_id: int


class ProjectBase(BaseModel):
    name: str
    batch_id: int


class ProjectCreate(ProjectBase):
    start_date: date
    end_date: date
    happy_hour: Optional[str] = None


class ProjectRead(ProjectBase):
    id: int
    start_date: date
    end_date: date
    happy_hour: Optional[str] = None

    class Config:
        from_attributes = True


class BatchBase(BaseModel):
    name: str
    slack_channel: str


class BatchCreate(BatchBase):
    start_date: date
    end_date: date
    curriculum: Optional[str] = None
    registration_key_active: Optional[bool] = True


class BatchRead(BatchBase):
    id: int
    start_date: date
    end_date: date
    slack_channel: str
    curriculum: Optional[str] = None
    registration_key: str
    registration_key_active: bool

    class Config:
        from_attributes = True


class BatchUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    slack_channel: Optional[str] = None
    curriculum: Optional[str] = None
    registration_key_active: Optional[bool] = None


class StudentBase(BaseModel):
    user_id: int
    batch_id: int
    project_id: Optional[int] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    batch_id: Optional[int] = None
    project_id: Optional[int] = None


class StudentRead(StudentBase):
    id: int

    class Config:
        from_attributes = True


class CertificateBase(BaseModel):
    name: str
    issuer: Optional[str] = None
    date_issued: Optional[date] = None
    date_expired: Optional[date] = None
    description: Optional[str] = None


class CertificateCreate(CertificateBase):
    pass


class CertificateUpdate(CertificateBase):
    name: Optional[str] = None
    pass


class CertificateRead(CertificateBase):
    id: int
    student_id: int

    class Config:
        from_attributes = True


class DemoBase(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[date] = None
    status: Optional[str] = "confirmed"


class DemoCreate(DemoBase):
    pass


class DemoUpdate(DemoBase):
    title: Optional[str] = None
    pass


class DemoRead(DemoBase):
    id: int
    student_id: int

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    happy_hour: Optional[str] = None
    batch_id: Optional[int] = None


# --- Demo Session Schemas ---
class DemoSessionBase(BaseModel):
    session_date: date
    is_active: bool = True
    is_cancelled: bool = False
    max_scheduled: Optional[int] = None
    title: Optional[str] = "Friday Demo Session"
    description: Optional[str] = None
    notes: Optional[str] = None


class DemoSessionCreate(DemoSessionBase):
    pass


class DemoSessionUpdate(BaseModel):
    session_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_cancelled: Optional[bool] = None
    max_scheduled: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class DemoSessionRead(DemoSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    signup_count: int = 0  # Will be populated via query
    signups: List["DemoSignupRead"] = []

    class Config:
        from_attributes = True


class DemoSessionSummary(BaseModel):
    """Lightweight version for listing sessions"""
    id: int
    session_date: date
    is_active: bool
    is_cancelled: bool
    max_scheduled: Optional[int] = None
    title: Optional[str] = None
    signup_count: int = 0
    user_scheduled: bool = False  # Will be populated based on current user

    class Config:
        from_attributes = True


# --- Demo Signup Schemas ---
class DemoSignupBase(BaseModel):
    demo_id: Optional[int] = None
    signup_notes: Optional[str] = None


class DemoSignupCreate(DemoSignupBase):
    pass


class DemoSignupUpdate(BaseModel):
    demo_id: Optional[int] = None
    signup_notes: Optional[str] = None


class DemoSignupRead(DemoSignupBase):
    id: int
    session_id: int
    student_id: int
    status: str
    did_present: Optional[bool] = None
    presentation_notes: Optional[str] = None
    presentation_rating: Optional[int] = None
    scheduled_at: datetime
    updated_at: datetime
    
    # Nested relationships
    student: Optional["StudentBasic"] = None
    demo: Optional["DemoRead"] = None

    class Config:
        from_attributes = True


class DemoSignupAdminUpdate(BaseModel):
    """Admin-specific fields for updating signup after presentation"""
    did_present: Optional[bool] = None
    presentation_notes: Optional[str] = None
    presentation_rating: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None


class StudentBasic(BaseModel):
    """Basic student info for nested relationships"""
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


# Update forward references
DemoSessionRead.model_rebuild()
DemoSignupRead.model_rebuild()
