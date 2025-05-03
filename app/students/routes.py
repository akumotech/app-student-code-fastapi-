from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.students.models import Student
from app.students.schemas import StudentCreate, StudentRead
from app.auth.database import engine

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# @router.post("/students/", response_model=StudentRead)
# def create_student(student: StudentCreate, session: Session = Depends(get_session)):
#     db_student = Student(user_id=student.user_id, batch=student.batch, project=student.project)
#     session.add(db_student)
#     session.commit()
#     session.refresh(db_student)
#     return db_student 