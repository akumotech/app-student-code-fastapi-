from pydantic import EmailStr, BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: EmailStr

class User(BaseModel):
    id: int
    email: EmailStr
    name: str
    disabled: bool | None = None
    wakatime_access_token_encrypted: Optional[str] = None
    wakatime_refresh_token_encrypted: Optional[str] = None

class UserInDB(User):
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    disabled: Optional[bool] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    is_student: Optional[bool] = False
    batch: Optional[str] = None
    project: Optional[str] = None