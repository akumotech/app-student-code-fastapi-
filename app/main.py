from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.auth.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

## local imports
from app.integrations.routes import router as integrations_router
from app.students.routes import router as students_router
from app.admin.routes import router as admin_router
from app.auth.utils import verify_access_token
from app.integrations.scheduler import start_scheduler
from app.config import settings
from app.analytics.routes import router as analytics_router

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Make EXCLUDE_PATHS a global or accessible constant for custom_openapi
EXCLUDE_PATHS_FOR_OPENAPI = [
    "/api/signup",
    "/api/login",
    "/docs",
    "/openapi.json",
    "/api/signup/student",
    # "/api/wakatime/fetch-manual" ## TESTING ONLY
]
# You might need to add other public paths if any, e.g. from integrations router if they are public
# Also, consider if the root path "/" or "/health" should be excluded.

app = FastAPI()

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        
        # Add HSTS in production
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://wakatime.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        
        return response

# Request size and security middleware
class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Check request size limit (10MB max)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return JSONResponse(
                status_code=413,
                content={"detail": "Request too large"}
            )
        
        # Check content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            allowed_types = [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data"
            ]
            if not any(allowed_type in content_type for allowed_type in allowed_types):
                return JSONResponse(
                    status_code=415,
                    content={"detail": "Unsupported content type"}
                )
        
        return await call_next(request)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://code.akumotechnology.com", # Production
        "https://code.dev.akumotechnology.com",
        "http://localhost:3000",  # For local development
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    start_scheduler()


app.include_router(auth_router, prefix="/api")
app.include_router(integrations_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(admin_router, prefix="/api/v1/admin")
app.include_router(analytics_router)

# Redefine EXCLUDE_PATHS for the middleware using the same source if possible,
# or ensure they are consistent.
EXCLUDE_PATHS_FOR_MIDDLEWARE = EXCLUDE_PATHS_FOR_OPENAPI  # Using the same list


class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        # Use the specific list for middleware
        if path in EXCLUDE_PATHS_FOR_MIDDLEWARE:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            verify_access_token(request)
            response = await call_next(request)
            return response
        except HTTPException as exc:
            return JSONResponse(
                content={"detail": exc.detail}, status_code=exc.status_code
            )
        except Exception as exc:
            # Log str(e) and traceback server-side
            print(f"Unhandled exception in CustomMiddleware: {exc}")
            return JSONResponse(
                content={"detail": "Internal server error"}, status_code=500
            )


app.add_middleware(CustomMiddleware)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="API with HTTP-Only Cookie Authentication",
        routes=app.routes,
    )
    # Define cookie-based security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "CookieAuth": {
            "type": "apiKey",
            "in": "cookie",
            "name": settings.ACCESS_TOKEN_COOKIE_NAME,
        }
    }
    # Apply security selectively
    for path_key, path_item in openapi_schema["paths"].items():
        if path_key not in EXCLUDE_PATHS_FOR_OPENAPI:
            for method in path_item.values():
                if isinstance(method, dict):
                    method["security"] = [{"CookieAuth": []}]
        else:
            for method in path_item.values():
                if isinstance(method, dict) and "security" in method:
                    method["security"] = []

    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi
