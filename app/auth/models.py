from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, Optional
from pydantic import EmailStr

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) ## id: int | None = Field(default=None, primary_key=True)
    email: EmailStr
    name: str
    disabled: Optional[bool] = False ## bool | None = False
    password: str
    wakatime_access_token_encrypted: Optional[str] = None
    wakatime_refresh_token_encrypted: Optional[str] = None
    role: Optional[str] = Field(default="none")  # 'student', 'instructor', 'admin', 'none'
    
    daily_summaries: List["DailySummary"] = Relationship(back_populates="user")
    