from pydantic import BaseModel
from typing import Optional
from datetime import date

class StudentCreate(BaseModel):
    user_id: int
    batch: str
    project: str

class StudentRead(BaseModel):
    id: int
    user_id: int
    batch: str
    project: str

class CertificateBase(BaseModel):
    name: str
    issuer: Optional[str] = None
    date_issued: Optional[date]
    date_expired: Optional[date]
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
    status: Optional[str] = "confirmed"

class DemoCreate(DemoBase):
    pass

class DemoUpdate(DemoBase):
    pass

class DemoRead(DemoBase):
    id: int
    class Config:
        orm_mode = True 