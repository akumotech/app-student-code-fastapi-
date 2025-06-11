from sqlmodel import Session

## local imports
from .models import User
from .security import pwd_context
from .schemas import UserCreate
from fastapi import HTTPException


def get_user_by_email(db: Session, email: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    return user


def create_user(db: Session, user_in: UserCreate, commit_session: bool = True) -> User:
    hashed_password = pwd_context.hash(user_in.password)
    user = User(
        email=user_in.email,
        name=user_in.name,
        password=hashed_password,
        disabled=user_in.disabled if user_in.disabled is not None else False,
        role="user",
    )
    db.add(user)
    if commit_session:
        try:
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error committing user creation: {str(e)}"
            )
    else:
        try:
            db.flush()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error flushing user data: {str(e)}"
            )
    return user


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
