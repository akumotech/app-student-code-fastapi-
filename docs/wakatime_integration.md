# WakaTime Integration: OAuth Connectivity & Database Involvement

## Overview

This document describes how the FastAPI backend integrates with WakaTime using OAuth, and how student connectivity is managed and stored in the database.

---

## 1. OAuth Flow for Student Connectivity

1. **Student Signup:**

   - User registers with their email and name.
   - If the user is a student, a `Student` record is created in the database, linked to the user.

2. **Initiate WakaTime Connection:**

   - User (student or regular) is directed to `/integrations/wakatime/authorize?email=...`.
   - This endpoint redirects the user to WakaTime's OAuth consent page.

3. **WakaTime Authorization:**

   - User authorizes the app to access their WakaTime data.
   - WakaTime redirects back to `/integrations/wakatime/callback?code=...&email=...`.

4. **Token Exchange & Storage:**

   - The backend exchanges the code for an access token.
   - The access token is encrypted and saved in the user's database record (`User` table).

5. **Data Access:**
   - The backend can use the stored access token to fetch the user's WakaTime data as needed.

---

## 2. Database Schema Involvement

### User Model

```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    name: str
    password: str
    wakatime_access_token_encrypted: Optional[str] = None  # Stores OAuth access token
    # ... other fields
```

### Student Model

```python
class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    batch: str
    project: str
    # ... other student-specific fields
```

- **wakatime_access_token_encrypted**: Now stored in the `User` table, not in `Student`.
- **Student**: Only contains a reference to the user and student-specific fields.

---

## 3. Security Considerations

- **Encryption:** All sensitive tokens are encrypted before being stored in the database using Fernet symmetric encryption.
- **Environment Variables:**
  - WAKATIME_CLIENT_ID and WAKATIME_CLIENT_SECRET are stored as environment variables.
  - The Fernet key is also stored as an environment variable for consistent encryption/decryption.
- **OAuth State:** In production, use a secure `state` parameter to prevent CSRF and securely link the OAuth flow to the correct user.

---

## 4. Checking Connectivity

- If `user.wakatime_access_token_encrypted` is not `None`, the user is considered connected to WakaTime.
- If it is `None`, the user has not connected or has disconnected.

---

## 5. Disconnecting

- To disconnect, simply remove or nullify the `wakatime_access_token_encrypted` field for the user.

---

## 6. Fetching WakaTime Data

- Decrypt the stored access token from the `User` table and use it in the `Authorization: Bearer ...` header when making API requests to WakaTime on behalf of the user.

---

## 7. Example Flow Diagram

```
User Signup  --->  User Record Created
      |
      v
(If student) Student Record Created
      |
      v
User Clicks "Connect WakaTime"
      |
      v
/integrations/wakatime/authorize?email=...
      |
      v
[WakaTime OAuth Consent]
      |
      v
/integrations/wakatime/callback?code=...&email=...
      |
      v
Access Token Saved (Encrypted in User)
      |
      v
Backend Can Fetch WakaTime Data
```

---

## 8. Future Improvements

- Use OAuth `state` for secure user association.
- Store and use refresh tokens for long-lived access.
- Add endpoints for disconnecting and reconnecting WakaTime accounts.
