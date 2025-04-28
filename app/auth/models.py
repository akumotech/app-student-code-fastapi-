from sqlmodel import Field, SQLModel
from typing import Optional

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    name: str
    disabled: bool | None = False
    password: str
    wakatime_access_token_encrypted: Optional[str] = None
    