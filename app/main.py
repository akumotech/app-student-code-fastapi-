from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.auth.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.openapi.utils import get_openapi

## local imports 
from app.auth.database import create_db_and_tables
from app.integrations.routes import router as integrations_router
from app.students.routes import router as students_router
from app.auth.utils import verify_access_token


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


app.include_router(auth_router)
app.include_router(integrations_router)
app.include_router(students_router)


EXCLUDE_PATHS = ["/signup", "/login", "/docs", "/openapi.json"]  # Add more if needed

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path in EXCLUDE_PATHS:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            # Call the verify_access_token function to validate the token
            verify_access_token(request)
            # If token validation succeeds, continue to the next middleware or route handler
            response = await call_next(request)
            return response
        except HTTPException as exc:
            # If token validation fails due to HTTPException, return the error response
            return JSONResponse(content={"detail": exc.detail}, status_code=exc.status_code)
        except Exception as exc:
            # If token validation fails due to other exceptions, return a generic error response
            return JSONResponse(content={"detail": f"Error: {str(exc)}"}, status_code=500)

# Add the custom middleware to the FastAPI app
app.add_middleware(CustomMiddleware)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="API with JWT auth",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema

app.openapi = custom_openapi