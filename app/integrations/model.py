from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, date

from app.auth.models import User


class WakaTimeCallbackPayload(BaseModel):
    code: str
    state: str | None = None


class WakaTimeStatsRangeRequest(BaseModel):
    start: str
    end: str


# WakaTimeUsageRequest is no longer used by routes.py, removed.
# class WakaTimeUsageRequest(BaseModel):
#     email: EmailStr


class DailySummary(SQLModel, table=True):
    # Consider adding __tablename__ = "daily_summary" for explicit naming
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")

    cached_at: datetime
    date: date
    start: datetime
    end: datetime
    timezone: str

    total_seconds: float
    hours: int
    minutes: int
    digital: str
    decimal: str
    text: str

    has_team_features: Optional[bool] = False

    user: Optional[User] = Relationship(back_populates="daily_summaries")

    # Detail relationships
    projects: List["WakaProject"] = Relationship(back_populates="summary")
    languages: List["Language"] = Relationship(back_populates="summary")
    dependencies: List["Dependency"] = Relationship(back_populates="summary")
    editors: List["Editor"] = Relationship(back_populates="summary")
    operating_systems: List["OperatingSystem"] = Relationship(back_populates="summary")
    machines: List["Machine"] = Relationship(back_populates="summary")
    categories: List["Category"] = Relationship(back_populates="summary")


class BaseDetail(SQLModel):  # Not a table itself
    name: str
    total_seconds: float
    digital: str
    decimal: str
    text: str
    hours: int
    minutes: int
    seconds: int
    percent: float


class WakaProject(BaseDetail, table=True):
    # Consider __tablename__ = "wakatime_project_details" or similar
    id: Optional[int] = Field(default=None, primary_key=True)
    summary_id: int = Field(
        foreign_key="dailysummary.id"
    )  # Assumes DailySummary table is 'dailysummary'
    summary: Optional[DailySummary] = Relationship(back_populates="projects")


class Language(BaseDetail, table=True):
    # Consider __tablename__ = "daily_summary_language"
    id: Optional[int] = Field(default=None, primary_key=True)
    summary_id: int = Field(foreign_key="dailysummary.id")
    summary: Optional[DailySummary] = Relationship(back_populates="languages")


class Dependency(BaseDetail, table=True):
    # Consider __tablename__ = "daily_summary_dependency"
    id: Optional[int] = Field(default=None, primary_key=True)
    summary_id: int = Field(foreign_key="dailysummary.id")
    summary: Optional[DailySummary] = Relationship(back_populates="dependencies")


class Editor(BaseDetail, table=True):
    # Consider __tablename__ = "daily_summary_editor"
    id: Optional[int] = Field(default=None, primary_key=True)
    summary_id: int = Field(foreign_key="dailysummary.id")
    summary: Optional[DailySummary] = Relationship(back_populates="editors")


class OperatingSystem(BaseDetail, table=True):
    # Consider __tablename__ = "daily_summary_os"
    id: Optional[int] = Field(default=None, primary_key=True)
    summary_id: int = Field(foreign_key="dailysummary.id")
    summary: Optional[DailySummary] = Relationship(back_populates="operating_systems")


class Machine(BaseDetail, table=True):
    # Consider __tablename__ = "daily_summary_machine"
    id: Optional[int] = Field(default=None, primary_key=True)
    machine_name_id: Optional[str]
    summary_id: int = Field(foreign_key="dailysummary.id")
    summary: Optional[DailySummary] = Relationship(back_populates="machines")


class Category(BaseDetail, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    summary_id: int = Field(foreign_key="dailysummary.id")
    summary: Optional[DailySummary] = Relationship(back_populates="categories")
