import os
import httpx
import secrets
import hashlib
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from app.integrations.wakatime import fetch_today_data, fetch_stats_range
from pydantic import BaseModel
from sqlmodel import Session, select
from app.auth.models import User
from app.auth.database import get_session
from app.auth.utils import get_current_active_user
from app.integrations.model import WakaTimeCallbackPayload, WakaTimeStatsRangeRequest
from app.config import settings
from app.auth.auth import APIResponse
# from app.integrations.scheduler import fetch_and_save_all_users_wakatime_data

router = APIRouter()

# In-memory state storage (in production, use Redis or database)
oauth_states = {}

def generate_oauth_state(user_id: int) -> str:
    """Generate a cryptographically secure OAuth state parameter"""
    # Generate random state
    random_state = secrets.token_urlsafe(32)
    
    # Create state with user context
    state_data = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
        "random": random_state
    }
    
    # Hash the state for security
    state_hash = hashlib.sha256(f"{user_id}:{random_state}".encode()).hexdigest()
    
    # Store temporarily (expires in 10 minutes)
    oauth_states[state_hash] = {
        "user_id": user_id,
        "expires": datetime.utcnow() + timedelta(minutes=10)
    }
    
    return state_hash

def validate_oauth_state(state: str, user_id: int) -> bool:
    """Validate OAuth state parameter"""
    if state not in oauth_states:
        return False
    
    stored_state = oauth_states[state]
    
    # Check expiration
    if datetime.utcnow() > stored_state["expires"]:
        del oauth_states[state]
        return False
    
    # Check user ID matches
    if stored_state["user_id"] != user_id:
        return False
    
    # Clean up used state
    del oauth_states[state]
    return True

## TESTING ONLY
# @router.post("/wakatime/fetch-manual")
# async def wakatime_fetch_manual():
#     await fetch_and_save_all_users_wakatime_data()
#     return {"status": "Triggered"}

@router.post(
    "/wakatime/today",
    response_model=APIResponse,
    summary="Get WakaTime data for today for authenticated user",
)
async def wakatime_today_for_user(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    if not current_user.wakatime_access_token_encrypted:
        return APIResponse(
            success=False, error="WakaTime token not found for user", data=None
        )

    try:
        data = await fetch_today_data(current_user, session)
        return APIResponse(
            success=True, message="WakaTime daily data fetched successfully.", data=data
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching WakaTime today data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching WakaTime data.",
        )


@router.post(
    "/wakatime/stats-range",
    response_model=APIResponse,
    summary="Get WakaTime stats for a date range",
)
async def wakatime_stats_range(
    request: WakaTimeStatsRangeRequest,
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session)
):
    if not current_user.wakatime_access_token_encrypted:
        return APIResponse(
            success=False, error="WakaTime token not found for user", data=None
        )

    try:
        data = await fetch_stats_range(current_user, session, request.start, request.end)
        return APIResponse(
            success=True, message="WakaTime stats fetched successfully.", data=data
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching WakaTime stats range: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching WakaTime stats.",
        )


@router.get(
    "/wakatime/authorize", summary="Initiate WakaTime OAuth for authenticated user"
)
async def wakatime_authorize_for_user(
    current_user: User = Depends(get_current_active_user),
):
    # Generate secure state parameter
    state_value = generate_oauth_state(current_user.id)

    scopes = "email,read_logged_time,read_stats"

    auth_url = (
        "https://wakatime.com/oauth/authorize"
        f"?client_id={settings.WAKATIME_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={settings.REDIRECT_URI}"
        f"&state={state_value}"
        f"&scope={scopes}"
    )
    return APIResponse(
        success=True,
        message="WakaTime authorization URL generated.",
        data={"authorization_url": auth_url},
    )


@router.post(
    "/wakatime/callback",
    response_model=APIResponse,
    summary="Handle WakaTime OAuth callback",
)
async def wakatime_callback(
    payload: WakaTimeCallbackPayload,  # Contains code and state from WakaTime
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    code = payload.code
    state_from_wakatime = payload.state

    # Debug logging
    print(f"WakaTime callback received for user {current_user.email}")
    print(f"Code length: {len(code) if code else 'None'}")
    print(f"State: {state_from_wakatime}")
    print(f"Redirect URI being used: {settings.REDIRECT_URI}")

    # Check if user already has a WakaTime token (prevent duplicate processing)
    if current_user.wakatime_access_token_encrypted:
        print(f"User {current_user.email} already has WakaTime token, callback may be duplicate")
        return APIResponse(
            success=True,
            message="WakaTime account already linked.",
            data={"status": "already_linked"},
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code from WakaTime callback",
        )

    # CRITICAL: Validate the state parameter using secure validation
    if not validate_oauth_state(state_from_wakatime, current_user.id):
        # Log this potential security event
        print(
            f"WakaTime callback state validation failed for user {current_user.email}. State: {state_from_wakatime}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired state parameter. Please restart the authorization process.",
        )

    # Exchange code for access token
    token_exchange_data = {
        "client_id": settings.WAKATIME_CLIENT_ID,
        "client_secret": settings.WAKATIME_CLIENT_SECRET,
        "redirect_uri": settings.REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    }
    
    # Debug logging for token exchange
    print(f"Token exchange data: {dict(token_exchange_data)}")
    print(f"Client ID: {settings.WAKATIME_CLIENT_ID[:10]}...")  # Only first 10 chars for security
    print(f"Redirect URI: {settings.REDIRECT_URI}")
    
    response_text_debug = "N/A"  # For debugging in case of early exit
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://wakatime.com/oauth/token",
                headers={"Accept": "application/json"},
                data=token_exchange_data,
            )
        response_text_debug = response.text  # Store for potential error logging

        if response.status_code != 200:
            # Log response.text for debugging server-side
            print(
                f"WakaTime token exchange failed. Status: {response.status_code}, Response: {response_text_debug}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # Or map to 502/503 if it's a WakaTime server issue
                detail="Failed to retrieve WakaTime access token from WakaTime.",
            )

        token_data = response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")  # WakaTime might provide this
        expires_in = token_data.get("expires_in")
        granted_scopes = token_data.get("scope")
        
      
        if refresh_token:
            print(f"- Refresh token length: {len(refresh_token)}")

        if not access_token:
            print(
                f"WakaTime token exchange succeeded but no access_token in response: {response_text_debug}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WakaTime access token not found in response.",
            )

    except httpx.HTTPError as e:
        print(f"HTTP error during WakaTime token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to communicate with WakaTime server.",
        )
    except Exception as e:
        print(f"Unexpected error during WakaTime token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error during WakaTime authorization.",
        )

    # Encrypt & save tokens to the already authenticated current_user
    # get_current_active_user provides a User model instance that should be session-aware.
    try:
        # Ensure current_user is part of the current session before modification
        # db_user = session.get(User, current_user.id) # This fetches a fresh instance
        # if not db_user: # Should not happen if current_user is valid
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Authenticated user not found in database for token update.")
        # For SQLAlchemy, modifications to `current_user` (if it's a session-managed object) are tracked.
        current_user.wakatime_access_token_encrypted = settings.fernet.encrypt(
            access_token.encode("utf-8")
        ).decode("utf-8")
        if refresh_token:
            # Ensure your User model in auth/models.py has wakatime_refresh_token_encrypted field
            current_user.wakatime_refresh_token_encrypted = settings.fernet.encrypt(
                refresh_token.encode("utf-8")
            ).decode("utf-8")
            print(f"Saved refresh token for user {current_user.email}")
        else:
            print(f"WARNING: No refresh token received for user {current_user.email}. Token refresh will not be available.")

        session.add(current_user)  # Add current_user to session to track changes
        session.commit()
        session.refresh(current_user)
    except Exception as e:
        session.rollback()
        # Log e server-side
        print(f"Error saving WakaTime tokens to database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save WakaTime integration details.",
        )

    return APIResponse(
        success=True,
        message="WakaTime account linked successfully.",
        data={"scopes": token_data.get("scope")},
    )
