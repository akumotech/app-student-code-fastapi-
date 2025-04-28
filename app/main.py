from fastapi import FastAPI
from app.auth.auth import router as auth_router
from fastapi.middleware.cors import CORSMiddleware
## local imports 
from app.auth.database import create_db_and_tables
from app.integrations.routes import router as integrations_router
from app.students.routes import router as students_router


app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth_router)
app.include_router(integrations_router)
app.include_router(students_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)