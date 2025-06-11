from pydantic import BaseModel
from typing import Optional, List
from datetime import date


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
    link: Optional[str] = None
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
