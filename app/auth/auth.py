from fastapi.security import OAuth2PasswordBearer
from fastapi import APIRouter, Depends, HTTPException, status, Response
from datetime import timedelta
from typing import Any

## local imports
from .schemas import (
    Token,
    UserInDB,
    User as UserSchema,
    LoginRequest,
    SignupRequest,
    UserCreate,
    StudentSignupRequest,
)
from .utils import create_access_token, authenticate_user, get_current_active_user
from app.config import settings
from .database import get_session, Session
from . import crud

# Assuming singular 'Student' model name from app.students.models as per best practice
from app.students.models import Student, Batch
from app.students import crud as students_crud
from app.students.schemas import StudentCreate as StudentCreateSchema
from .models import User
from app.core.schemas import APIResponse

router = APIRouter()


@router.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: UserSchema = Depends(get_current_active_user)):
    return current_user


@router.post("/login")
async def login(
    data: LoginRequest, response: Response, db: Session = Depends(get_session)
):
    user = await authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Set the access token in an HTTP-only cookie
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=int(access_token_expires.total_seconds()),  # in seconds
        expires=access_token_expires,  # also set expires for older browsers
        path="/",
        secure=settings.COOKIE_SECURE,  # From config, True in prod over HTTPS
        samesite=settings.COOKIE_SAMESITE,  # From config, e.g., "lax" or "strict"
    )

    # Return user info in the response body, token is now in cookie
    api_response_data = APIResponse(
        success=True,
        message="Login successful",
        data={
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            }
        },
    )
    return api_response_data


@router.post("/signup", response_model=APIResponse)
async def signup(data: SignupRequest, db: Session = Depends(get_session)):
    if crud.get_user_by_email(db, email=data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user_create_data = UserCreate(
        email=data.email, name=data.name, password=data.password
    )
    # crud.create_user now defaults to commit_session=True, which is fine for this standard signup.
    user = crud.create_user(db, user_in=user_create_data)

    return APIResponse(
        success=True,
        message="Signup successful. If you are a student, please complete student registration.",
        data={
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
        },
    )


@router.post(
    "/signup/student",
    response_model=APIResponse,
    summary="Student Signup with Batch Key",
)
async def student_signup_with_key(
    data: StudentSignupRequest, db: Session = Depends(get_session)
):
    # 1. Verify batch registration key
    batch = (
        db.query(Batch)
        .filter(Batch.registration_key == data.batch_registration_key)
        .first()
    )
    if not batch or not batch.registration_key_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive batch registration key.",
        )

    # 2. Check if user already exists
    if crud.get_user_by_email(db, email=data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    try:
        # 3. Create User with role 'student'
        # crud.create_user is expected to handle password hashing
        # Forcing role to 'student' here
        user_create_data = UserCreate(
            email=data.email, name=data.name, password=data.password
        )
        # Explicitly set role before passing to crud.create_user or modify crud.create_user
        # For now, we'll create, then update role as part of the transaction.

        new_user = crud.create_user(
            db, user_in=user_create_data, commit_session=False
        )  # Pass commit_session=False
        new_user.role = "student"  # Set role
        db.add(
            new_user
        )  # Add to session again if role was modified on an instance from create_user
        # that didn't commit.

        # 4. Create Student Profile
        # project_id can be None if not applicable at this stage
        student_profile_data = StudentCreateSchema(
            user_id=new_user.id, batch_id=batch.id, project_id=None
        )
        new_student_profile = students_crud.create_student(
            db, student_create=student_profile_data
        )
        # students_crud.create_student uses flush, not commit.

        db.commit()
        db.refresh(new_user)
        db.refresh(new_student_profile)

    except HTTPException:  # Re-raise HTTPExceptions
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Log the exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not complete student signup. Please try again later.",
        )

    return APIResponse(
        success=True,
        message="Student signup successful. You are now registered as a student in the batch.",
        data={
            "user": {
                "id": new_user.id,
                "email": new_user.email,
                "name": new_user.name,
                "role": new_user.role,
            },
            "student_profile": {
                "id": new_student_profile.id,
                "batch_id": new_student_profile.batch_id,
            },
        },
    )


@router.post("/students/register", response_model=APIResponse)
async def register_student(
    user_id: int,
    batch_id: int,
    project_id: int,
    db: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    # Authorization: Ensure the logged-in user is the one being registered or an admin.
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to register this user as a student",
        )

    db_user_to_register = db.query(User).filter(User.id == user_id).first()
    if not db_user_to_register:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found",
        )

    # Check if a student record already exists for this user_id
    existing_student = db.query(Student).filter(Student.user_id == user_id).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user_id} is already registered as a student.",
        )

    # TODO: Optionally, verify that batch_id and project_id exist before creating the student record
    # batch = db.query(Batch).filter(Batch.id == batch_id).first()
    # if not batch: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch {batch_id} not found")
    # project = db.query(Project).filter(Project.id == project_id).first()
    # if not project: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found")

    # Create the student record
    student = Student(user_id=user_id, batch_id=batch_id, project_id=project_id)
    db.add(student)

    # Update user's role to 'student'
    db_user_to_register.role = "student"
    db.add(db_user_to_register)

    try:
        db.commit()
        db.refresh(student)
        db.refresh(db_user_to_register)
    except Exception as e:
        db.rollback()
        # Consider logging the exception e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not register student. Please try again later.",
        )

    return APIResponse(
        success=True,
        message="Student registered successfully and user role updated.",
        data={
            "student_id": student.id,
            "user_id": db_user_to_register.id,
            "name": db_user_to_register.name,
            "role": db_user_to_register.role,
        },
    )


@router.post("/logout", response_model=APIResponse)
async def logout(response: Response):
    # Clear the access token cookie
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value="",  # Empty value
        httponly=True,
        max_age=0,  # Expire immediately
        expires=0,  # Expire immediately (for older browsers)
        path="/",
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
    )
    return APIResponse(success=True, message="Successfully logged out.")
