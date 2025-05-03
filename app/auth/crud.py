from sqlmodel import Session
## local imports
from .models import User
from .security import pwd_context


def get_user_by_email(db: Session, email: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    return user

def create_user(db: Session, email: str, password: str, name: str, disabled: bool = False):
    try:
        hashed_password = pwd_context.hash(password)
        user = User(
            email=email,
            name=name,
            password=hashed_password,
            disabled=disabled
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Error creating user: {str(e)}"
        )