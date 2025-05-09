from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
## local imports
from .schemas import Token, UserInDB, User, LoginRequest, SignupRequest, UserCreate
from .utils import create_access_token, authenticate_user, get_current_active_user
from app.config import settings
from .database import get_session
from . import crud, models, schemas
from app.students.models import Student
router = APIRouter()

@router.get("/users/me/", response_model=None)
async def read_users_me(
    current_user = Depends(get_current_active_user), 
    db: Session = Depends(get_session)
):
    return current_user


@router.post("/login")
async def login(data: LoginRequest, db: Session = Depends(get_session)):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        return {
            "ok": False,
            "message": "Invalid credentials",
            "error": "Login failed"
        }
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {
        "ok": True,
        "message": "Login successful",
        "payload": {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }
    }

@router.post("/signup")
async def signup(data: SignupRequest, db: Session = Depends(get_session)):
    if crud.get_user_by_email(db, data.email):
        return {
            "ok": False,
            "message": "Email already registered",
            "error": "Signup failed"
        }
    user = crud.create_user(db, email=data.email, name=data.name, password=data.password)
    if data.is_student and data.batch and data.project:
        student = Student(user_id=user.id, batch=data.batch, project=data.project)
        db.add(student)
        db.commit()
        db.refresh(student)
    return {
        "ok": True,
        "message": "Signup successful"
    }

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out."}