from fastapi import HTTPException, status, Depends, Request, Response
from fastapi.security import OAuth2PasswordBearer, APIKeyCookie
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

## local imports
from .schemas import TokenData, UserInDB, User as UserSchema
from app.config import settings  # SECRET_KEY, ALGORITHM
from .crud import get_user_by_email
from .security import pwd_context
from .database import get_session
from app.students.models import BatchInstructorLink, BatchStudentLink

# This scheme is no longer the primary way to get the token for get_current_active_user
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Custom dependency to get token from HTTP-only cookie
# The `scheme_name` can be anything, it's for documentation purposes.
# `name` is the actual cookie name.
access_token_cookie_scheme = APIKeyCookie(
    name=settings.ACCESS_TOKEN_COOKIE_NAME, auto_error=False
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(*, data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=15
        )  # Default expiry if none provided
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str | None = Depends(access_token_cookie_scheme),
    db: Session = Depends(get_session),
) -> UserSchema | None:
    if token is None:
        # This will be handled by get_current_active_user if it needs to raise an error for missing token
        return None

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Cookie"},  # Indicate cookie auth
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserSchema | None = Depends(get_current_user),
) -> UserSchema:
    if (
        current_user is None
    ):  # Explicitly check if token was not found or invalid from get_current_user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"},  # Indicate cookie auth
        )
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


# verify_access_token for middleware will also need to change
# This function was used by main.py CustomMiddleware
def verify_access_token(request: Request):
    token = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (no token in cookie)",
            headers={"WWW-Authenticate": "Cookie"},
        )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )
        # Optionally, could fetch user from DB here to ensure they still exist/active,
        # but get_current_active_user does that for protected routes.
        # For middleware, just verifying token validity might be enough if performance is key.
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate token"
        )


# authenticate_user function remains unchanged for now
async def authenticate_user(db: Session, email: str, password: str) -> UserInDB | None:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not pwd_context.verify(password, user.password):
        return None
    return user
