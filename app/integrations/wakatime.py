import httpx
import os
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.auth.models import User
from sqlmodel import Session
from app.config import settings


async def refresh_wakatime_token(user: User, session: Session) -> str:
    """Refresh WakaTime access token using refresh token. Does NOT commit session."""
    if not user.wakatime_refresh_token_encrypted:
        # Log this issue: User has access token but no refresh token to use.
        print(
            f"User {user.email} attempted WakaTime token refresh without a refresh token."
        )
        # Clear the access token as well since we can't refresh it
        user.wakatime_access_token_encrypted = None
        session.add(user)
        session.commit()
        raise HTTPException(
            status_code=400,
            detail="WakaTime refresh token not available. Please re-authorize.",
        )

    try:
        refresh_token = settings.fernet.decrypt(
            user.wakatime_refresh_token_encrypted.encode("utf-8")
        ).decode("utf-8")
        print(f"Successfully decrypted refresh token for user {user.email}")
    except Exception as e:
        # Log decryption error
        print(f"Error decrypting WakaTime refresh token for user {user.email}: {e}")
        # Clear invalid tokens
        user.wakatime_access_token_encrypted = None
        user.wakatime_refresh_token_encrypted = None
        session.add(user)
        session.commit()
        raise HTTPException(
            status_code=500,
            detail="Failed to process WakaTime refresh token. Please re-authorize.",
        )

    data = {
        "client_id": settings.WAKATIME_CLIENT_ID,
        "client_secret": settings.WAKATIME_CLIENT_SECRET,
        "redirect_uri": settings.REDIRECT_URI,  # Ensure this is the same redirect_uri used in initial auth
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response_text_debug = "N/A"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("https://wakatime.com/oauth/token", data=data)
        response_text_debug = response.text
        response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses
        token_data = response.json()
    except httpx.HTTPStatusError as exc:
        # Log specific HTTP error from WakaTime
        print(
            f"WakaTime token refresh failed. Status: {exc.response.status_code}, Response: {exc.response.text}"
        )
        # If 400/401, often means bad refresh token -> re-auth needed
        if exc.response.status_code in [400, 401]:
            # Clear invalid tokens from database
            print(f"Clearing invalid WakaTime tokens for user {user.email}")
            user.wakatime_access_token_encrypted = None
            user.wakatime_refresh_token_encrypted = None
            session.add(user)
            session.commit()
            
            raise HTTPException(
                status_code=400,
                detail="WakaTime tokens are invalid. Please re-authorize WakaTime integration.",
            )
        raise HTTPException(
            status_code=502,
            detail="Error communicating with WakaTime for token refresh.",
        )  # Bad Gateway for upstream error
    except httpx.RequestError as exc:
        print(f"Request to WakaTime /oauth/token for refresh failed: {exc}")
        raise HTTPException(
            status_code=503, detail="Could not connect to WakaTime to refresh token."
        )
    except Exception as exc:  # Includes JSONDecodeError
        print(
            f"Unexpected error during WakaTime token refresh: {exc}, Response text: {response_text_debug}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during WakaTime token refresh.",
        )

    new_access_token = token_data.get("access_token")
    new_refresh_token = token_data.get("refresh_token")

    if not new_access_token:
        print(f"WakaTime access_token not found in refresh response: {token_data}")
        raise HTTPException(
            status_code=500,
            detail="WakaTime did not return an access token on refresh.",
        )

    user.wakatime_access_token_encrypted = settings.fernet.encrypt(
        new_access_token.encode("utf-8")
    ).decode("utf-8")
    if new_refresh_token:
        user.wakatime_refresh_token_encrypted = settings.fernet.encrypt(
            new_refresh_token.encode("utf-8")
        ).decode("utf-8")
        print(f"Updated refresh token for user {user.email}")
    else:
        print(f"WARNING: No new refresh token received for user {user.email}")

    session.add(user)  # Mark user as dirty for the calling session to commit
    # DO NOT COMMIT HERE
    print(f"Token refresh successful for user {user.email}")
    return new_access_token


async def wakatime_api_request(
    user: User, session: Session, method: str, url: str, **kwargs
):
    """Make an authenticated WakaTime API request (async), auto-refreshing if needed."""
    if not user.wakatime_access_token_encrypted:
        raise HTTPException(
            status_code=401,
            detail="WakaTime access token not available. Please authorize WakaTime integration.",
        )

    try:
        access_token = settings.fernet.decrypt(
            user.wakatime_access_token_encrypted.encode("utf-8")
        ).decode("utf-8")
    except Exception as e:
        print(f"Error decrypting WakaTime access token for user {user.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process WakaTime access token. Please re-authorize.",
        )

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient() as client:
        response = await client.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:  # Token expired or invalid
            print(
                f"WakaTime API request got 401 for user {user.email}. Attempting token refresh."
            )
            try:
                new_access_token = await refresh_wakatime_token(user, session)
                # Commit the token changes
                session.commit()
                headers["Authorization"] = f"Bearer {new_access_token}"
                # Retry the request with the new token
                response = await client.request(method, url, headers=headers, **kwargs)
            except HTTPException as he:  # Catch errors from refresh_wakatime_token
                # If refresh itself fails (e.g. bad refresh token, WakaTime down), propagate the error
                raise he

        response.raise_for_status()  # Raise an exception for 4xx/5xx status codes if not handled above
        return response.json()  # Return JSON decoded response


async def fetch_today_data(user: User, session: Session):
    """Fetch today's WakaTime summary for user."""
    url = "https://wakatime.com/api/v1/users/current/status_bar/today"
    return await wakatime_api_request(user, session, "GET", url)


async def fetch_stats_range(user: User, session: Session, start: str, end: str):
    """Fetch WakaTime stats for a specified date range."""
    url = (
        f"https://wakatime.com/api/v1/users/current/summaries"
        f"?start={start}&end={end}"
    )
    return await wakatime_api_request(user, session, "GET", url)


# fetch_stats_data function (for last_7_days) can be kept if used elsewhere or removed if redundant
# async def fetch_stats_data(user: User, session: Session):
#     """Fetch WakaTime last 7 days stats for user."""
#     url = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
#     return await wakatime_api_request(user, session, "GET", url)
