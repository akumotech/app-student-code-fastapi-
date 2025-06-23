from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime


class UserRoleUpdate(BaseModel):
    role: str


class StudentUpdate(BaseModel):
    batch_id: Optional[int] = None
    project_id: Optional[int] = None


class UserBasic(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    disabled: bool

    class Config:
        from_attributes = True


class CertificateInfo(BaseModel):
    id: int
    name: str
    issuer: Optional[str] = None
    date_issued: Optional[date] = None
    date_expired: Optional[date] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class DemoInfo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    link: Optional[str] = None
    demo_date: Optional[date] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class BatchInfo(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    slack_channel: str
    curriculum: Optional[str] = None
    registration_key: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectInfo(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    happy_hour: Optional[str] = None

    class Config:
        from_attributes = True


class WakaTimeStats(BaseModel):
    total_seconds: float
    hours: int
    minutes: int
    digital: str
    text: str
    last_updated: Optional[datetime] = None


class StudentDetail(BaseModel):
    id: int
    user: UserBasic
    batch: Optional[BatchInfo] = None
    project: Optional[ProjectInfo] = None
    certificates: List[CertificateInfo] = []
    demos: List[DemoInfo] = []
    wakatime_stats: Optional[WakaTimeStats] = None

    class Config:
        from_attributes = True


class UserOverview(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    disabled: bool
    student_detail: Optional[StudentDetail] = None
    wakatime_connected: bool = False
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_users: int
    total_students: int
    total_instructors: int
    total_admins: int
    active_batches: int
    total_certificates: int
    total_demos: int
    users_with_wakatime: int


class AdminUsersList(BaseModel):
    users: List[UserOverview]
    total_count: int
    page: int
    page_size: int


class AdminDashboard(BaseModel):
    stats: DashboardStats
    recent_students: List[UserOverview]
    active_batches: List[BatchInfo]
