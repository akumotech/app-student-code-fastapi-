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
    role: str
    disabled: bool | None = None
    wakatime_access_token_encrypted: Optional[str] = None
    wakatime_refresh_token_encrypted: Optional[str] = None
    student_id: Optional[int] = None # This is only for admin users

    class Config:
        from_attributes = True


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


class StudentSignupRequest(SignupRequest):
    batch_registration_key: str
