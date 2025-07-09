# 🛡️ FastAPI User & Student Management with WakaTime Integration

A modern backend built with **FastAPI**, featuring:

- JWT-based token auth (`OAuth2PasswordBearer`)
- Password hashing with **bcrypt**
- PostgreSQL/SQLModel user database
- Student management (batch, project, etc.)
- WakaTime OAuth integration for code activity tracking
- Protected routes

## 🚀 Getting Started

### Running the Application

1. **Prepare the Environment**  
   Ensure you have Python 3.11+ and PostgreSQL running.

2. **Install Project Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**

   - `WAKATIME_CLIENT_ID` and `WAKATIME_CLIENT_SECRET` (from your WakaTime app)
   - `FERNET_KEY` (for encrypting tokens)

4. **Start the Server**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

Visit: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to test the API using the Swagger UI.

---

## 🏗️ Architecture Overview

- **User**: All users (students and regular users). Stores identity info and WakaTime access token.
- **Student**: Linked to a user. Stores student-specific info (batch, project, etc.).
- **WakaTime Integration**: Users can connect their WakaTime account via OAuth. Access token is stored (encrypted) in the User model.

---

## 📂 Endpoints Overview

| Method | Endpoint                           | Description                                 |
| ------ | ---------------------------------- | ------------------------------------------- |
| POST   | `/api/auth`                        | Log in, get JWT token                       |
| POST   | `/api/users`                       | Register a new user (optionally as student) |
| POST   | `/api/logout`                      | Log out (stateless)                         |
| GET    | `/api/users/me/`                   | Get current user info                       |
| POST   | `/students/`                       | (Admin/future) Create student               |
| POST   | `/integrations/wakatime/usage`     | Fetch WakaTime stats for a user             |
| GET    | `/integrations/wakatime/authorize` | Start WakaTime OAuth flow                   |
| GET    | `/integrations/wakatime/callback`  | Handle WakaTime OAuth callback              |

---

## 📝 Example Requests

### Signup (Regular User)

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"testpass"}'
```

### Signup (Student)

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com","name":"Student User","password":"testpass","is_student":true,"batch":"April-2025","project":"Project 11"}'
```

### Connect WakaTime (OAuth)

1. Direct user to:
   ```
   /integrations/wakatime/authorize?email=student@example.com
   ```
2. User authorizes and is redirected to `/integrations/wakatime/callback`.
3. Access token is saved (encrypted) in the User model.

### Fetch WakaTime Usage

```bash
curl -X POST http://localhost:8000/integrations/wakatime/usage \
  -H "Content-Type: application/json" \
  -d '{"email":"student@example.com"}'
```

---

## 🔒 Security Notes

- Passwords are hashed using **bcrypt**
- JWT tokens use **HS256**
- Tokens expire after **60 minutes**
- WakaTime access tokens are encrypted with Fernet
- **Email** is used as the unique user identifier

---

## 🧠 TODO

- Add refresh token mechanism
- Add user profile update/delete
- Add email verification
- Add admin endpoints for managing students
- Add support for WakaTime refresh tokens

---

**License:** MIT  
**Author:** @copypasteninja
