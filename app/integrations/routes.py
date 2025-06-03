import os
import httpx
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from app.integrations.wakatime import fetch_today_data, fetch_stats_range
from pydantic import BaseModel
from sqlmodel import Session, select
from app.auth.models import User
from app.auth.database import get_session
from app.auth.utils import get_current_active_user
from app.integrations.model import WakaTimeCallbackPayload
from app.config import settings
from app.auth.auth import APIResponse

router = APIRouter()


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
    "/wakatime/usage",
    response_model=APIResponse,
    summary="Get WakaTime usage stats for authenticated user",
)
async def wakatime_usage_for_user(
    current_user: User = Depends(get_current_active_user),
    session: Session = Depends(get_session),
):
    if not current_user.wakatime_access_token_encrypted:
        return APIResponse(
            success=False, error="WakaTime token not found for user", data=None
        )

    try:
        data = await fetch_stats_range(current_user, session)
        return APIResponse(
            success=True, message="WakaTime usage data fetched successfully.", data=data
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error fetching WakaTime usage data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching WakaTime usage data.",
        )


@router.get(
    "/wakatime/authorize", summary="Initiate WakaTime OAuth for authenticated user"
)
async def wakatime_authorize_for_user(
    current_user: User = Depends(get_current_active_user),
):
    state_value = current_user.email

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

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code from WakaTime callback",
        )

    # CRITICAL: Verify the state to prevent CSRF and ensure user consistency.
    # The state sent to WakaTime during /authorize should match what's received here.
    # Assuming state was current_user.email (or str(current_user.id)).
    expected_state = current_user.email  # Or str(current_user.id) if that was used
    if state_from_wakatime != expected_state:
        # Log this potential security event
        print(
            f"WakaTime callback state mismatch for user {current_user.email}. Expected: {expected_state}, Got: {state_from_wakatime}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid state parameter. WakaTime authorization may be compromised.",
        )

    # Exchange code for access token
    token_exchange_data = {
        "client_id": settings.WAKATIME_CLIENT_ID,
        "client_secret": settings.WAKATIME_CLIENT_SECRET,
        "redirect_uri": settings.REDIRECT_URI,
        "grant_type": "authorization_code",
        "code": code,
    }
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
        # expires_in = token_data.get("expires_in") # And expiry
        # granted_scopes = token_data.get("scope")
    except httpx.RequestError as exc:
        # Log exc for debugging server-side
        print(f"Request to WakaTime /oauth/token failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to WakaTime to exchange token.",
        )
    except Exception as exc:  # Catch other errors like JSONDecodeError
        print(
            f"Error during WakaTime token exchange or JSON parsing: {exc}, Response text: {response_text_debug}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during WakaTime token exchange.",
        )

    if not access_token:
        # Log token_data for debugging
        print(f"WakaTime access_token not found in response: {token_data}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token not found in WakaTime's response",
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
