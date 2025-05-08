from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, Optional

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    name: str
    disabled: bool | None = False
    password: str
    wakatime_access_token_encrypted: Optional[str] = None
    
    daily_summaries: List["DailySummary"] = Relationship(back_populates="user")
    