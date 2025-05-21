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
    start_date: date
    end_date: date
    happy_hour: Optional[str] = None
    batch_id: int

class ProjectCreate(ProjectBase):
    pass

class ProjectRead(ProjectBase):
    id: int
    class Config:
        orm_mode = True

class BatchBase(BaseModel):
    name: str
    start_date: date
    end_date: date
    slack_channel: str
    curriculum: Optional[str] = None

class BatchCreate(BatchBase):
    pass

class BatchRead(BatchBase):
    id: int
    class Config:
        orm_mode = True

class StudentCreate(BaseModel):
    user_id: int
    batch_id: int
    project_id: int

class StudentRead(BaseModel):
    id: int
    user_id: int
    batch_id: int
    project_id: int

class CertificateBase(BaseModel):
    name: str
    issuer: Optional[str] = None
    date_issued: Optional[date] = None
    date_expired: Optional[date] = None
    description: Optional[str] = None

class CertificateCreate(CertificateBase):
    pass

class CertificateUpdate(CertificateBase):
    pass

class CertificateRead(CertificateBase):
    id: int
    class Config:
        orm_mode = True

class DemoBase(BaseModel):
    title: str
    description: Optional[str] = None
    link: Optional[str] = None
    date: Optional[date] = None

class DemoCreate(DemoBase):
    pass

class DemoUpdate(DemoBase):
    pass

class DemoRead(DemoBase):
    id: int
    class Config:
        orm_mode = True 