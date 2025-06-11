# Authentication System: HTTP-Only Cookie-Based

## Overview

To enhance security, particularly against Cross-Site Scripting (XSS) attacks, our application has transitioned from using Bearer tokens in the `Authorization` header to an HTTP-only cookie-based authentication system for managing access tokens.

This document outlines the new authentication flow and provides details for frontend and backend developers.

## Key Changes & Flow

1.  **Token Storage**: The primary access token (JWT) is no longer sent in the JSON response of the login endpoint. Instead, it is stored in an HTTP-only cookie.
2.  **Automatic Token Sending**: Browsers automatically include this cookie in subsequent requests to the backend, eliminating the need for frontend JavaScript to manage or attach tokens to headers.

### 1. Login Endpoint (`/login`)

- **Method**: `POST`
- **Request**: Expects user credentials (e.g., email and password) in the request body.
- **On Successful Authentication**:
  - The backend generates a JWT access token.
  - This access token is set in an HTTP-only cookie on the user's browser.
  - The JSON response **will not** contain the `token` in its body.
  - The JSON response **will** contain user information (e.g., user ID, email, name, role) for the frontend to update its state.
- **Cookie Attributes**:
  - `HttpOnly`: `True` (Prevents access from client-side JavaScript)
  - `Secure`: Configurable via `settings.COOKIE_SECURE`. Should be `True` in production (requires HTTPS) and can be `False` for HTTP development environments.
  - `SameSite`: Configurable via `settings.COOKIE_SAMESITE` (e.g., `"Lax"` or `"Strict"`). `"Lax"` is the current default.
  - `Path`: `/` (Cookie is sent for all paths on the domain).
  - `Max-Age` / `Expires`: Set according to `settings.ACCESS_TOKEN_EXPIRE_MINUTES`.
- **Example Cookie Name**: `access_token_cookie` (configurable via `settings.ACCESS_TOKEN_COOKIE_NAME`).

### 2. Logout Endpoint (`/logout`)

- **Method**: `POST`
- **Action**:
  - Clears the access token cookie by setting its value to empty and its `Max-Age` to `0` (or an expiration date in the past).
  - The same `HttpOnly`, `Secure`, `SameSite`, and `Path` attributes are used when clearing to ensure the correct cookie is targeted.
- **Response**: A success message.

### 3. Accessing Protected Endpoints

- Any endpoint requiring authentication (e.g., `/users/me`, `/wakatime/usage`, etc.) now relies on the browser automatically sending the access token cookie.
- The backend extracts the JWT from this cookie to authenticate and authorize the request.
- If the cookie is missing, invalid, or expired, a `401 Unauthorized` error is returned.
- The `WWW-Authenticate` header in a `401` response will indicate `Cookie` to hint at the expected authentication method.

### 4. Middleware Authentication

The global authentication middleware (`CustomMiddleware` in `main.py`) has also been updated to inspect the access token cookie for all relevant requests, excluding paths like `/login`, `/signup`, `/docs`, etc.

## Refresh Tokens (Phase 2 - Coming Soon)

To provide a better user experience by allowing longer sessions without compromising access token security (which remain short-lived), a refresh token mechanism will be implemented:

- Refresh tokens will also be stored in a separate, long-lived HTTP-only cookie.
- A dedicated endpoint (e.g., `/refresh_token`) will allow exchanging a valid refresh token for a new access token (and potentially a new refresh token).
- This will be detailed further once implemented.

## Notes for Frontend Developers

- **Token Management**: You no longer need to store the access token in JavaScript variables, `localStorage`, or `sessionStorage`.
- **API Requests**: You do not need to manually attach an `Authorization: Bearer <token>` header to your API requests. The browser will handle sending the cookie automatically.
- **Login Response**: Adapt to receive user details from the login response body and rely on the cookie being set for session management.
- **Logout**: Call the `/logout` endpoint. The browser will process the cookie-clearing instructions from the backend.
- **Cross-Origin Resource Sharing (CORS)**:
  - If the frontend and backend are on different origins (e.g., `http://localhost:3000` for frontend, `http://localhost:8000` for backend), ensure the backend's CORS policy includes:
    - `allow_credentials=True`
    - The frontend's specific origin in `allow_origins`.
  - This is crucial for the browser to send cookies with cross-origin requests.

## Security Benefits

- **Mitigates XSS**: Prevents client-side JavaScript from accessing the access token, a common vector for token theft.
- **Secure Flag**: Ensures the token is only transmitted over HTTPS when enabled.
- **SameSite Attribute**: Provides a level of CSRF protection.

This transition significantly enhances the security posture of our application's authentication system.
