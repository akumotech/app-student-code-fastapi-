import os
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
import httpx
from app.integrations.wakatime import get_wakatime_stats
from pydantic import BaseModel
from sqlmodel import Session, select
from app.auth.models import User
from app.auth.database import engine
from cryptography.fernet import Fernet
from app.auth.utils import get_current_active_user

router = APIRouter()

WAKATIME_CLIENT_ID = os.getenv("WAKATIME_CLIENT_ID")
WAKATIME_CLIENT_SECRET = os.getenv("WAKATIME_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/wakatime/callback"
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key())
fernet = Fernet(FERNET_KEY)

def get_session():
    with Session(engine) as session:
        yield session

class WakaTimeUsageRequest(BaseModel):
    email: str

@router.post("/wakatime/usage")
def wakatime_usage(data: WakaTimeUsageRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or not user.wakatime_access_token_encrypted:
        raise HTTPException(status_code=404, detail="User or WakaTime token not found")
    access_token = fernet.decrypt(user.wakatime_access_token_encrypted.encode()).decode()
    try:
        stats = get_wakatime_stats(access_token)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wakatime/authorize")
def wakatime_authorize(email: str):
    # Store email using state parameter
    url = (
        "https://wakatime.com/oauth/authorize"
        f"?client_id={WAKATIME_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={email}"
        "&scope=read_logged_time"
    )
    return url

@router.get("/wakatime/callback")
async def wakatime_callback(request: Request, session: Session = Depends(get_session), current_user: User = Depends(get_current_active_user)):
    code = request.query_params.get("code")
    email = request.query_params.get("state")  # Get email from state
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Continue as before...
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://wakatime.com/oauth/token",
            data={
                "client_id": WAKATIME_CLIENT_ID,
                "client_secret": WAKATIME_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,  # No email parameter here
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        token_data = response.json()
        # Find the user by email and store the access token
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.wakatime_access_token_encrypted = fernet.encrypt(token_data["access_token"].encode()).decode()
        session.add(user)
        session.commit()
        return {"message": "WakaTime access token saved for user.", "user_email": email}