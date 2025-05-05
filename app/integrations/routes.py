import os
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from app.integrations.wakatime import get_wakatime_stats
from pydantic import BaseModel
from sqlmodel import Session, select
from app.auth.models import User
from app.auth.database import engine
from cryptography.fernet import Fernet
from app.auth.utils import get_current_active_user
from app.integrations.model import WakaTimeCallbackPayload, WakaTimeUsageRequest

router = APIRouter()

WAKATIME_CLIENT_ID = os.getenv("WAKATIME_CLIENT_ID")
WAKATIME_CLIENT_SECRET = os.getenv("WAKATIME_CLIENT_SECRET")
REDIRECT_URI = f"https://{os.getenv(FRONTEND_DOMAIN)}/callback"
FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key())
fernet = Fernet(FERNET_KEY)

def get_session():
    with Session(engine) as session:
        yield session

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

@router.post("/wakatime/callback")
async def wakatime_callback(
    payload: WakaTimeCallbackPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    code = payload.code
    state = payload.state  # You can use it if needed

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")


    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://wakatime.com/oauth/token",
            data={
                "client_id": WAKATIME_CLIENT_ID,
                "client_secret": WAKATIME_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
                "code": code,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to retrieve WakaTime access token"
            )

        token_data = response.json()

        # user = session.exec(select(User).where(User.email == email)).first()
        # if not user:
        #     raise HTTPException(status_code=404, detail="User not found")
        current_user.wakatime_access_token_encrypted = fernet.encrypt(token_data["access_token"].encode()).decode()
        session.add(current_user)
        session.commit()
        return {"message": "WakaTime access token saved for user.", "user_email": email}