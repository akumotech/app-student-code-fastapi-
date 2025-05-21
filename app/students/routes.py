from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from app.students.models import Students, Certificates, Demos, Batches, Projects
from app.students.schemas import (
    StudentCreate, StudentRead,
    CertificateCreate, CertificateUpdate, CertificateRead,
    DemoCreate, DemoUpdate, DemoRead,
    BatchCreate, BatchRead, ProjectCreate, ProjectRead
)
from app.auth.database import engine
from app.students import crud

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# --- Batch Endpoints ---
@router.post("/batches/", response_model=BatchRead)
def create_batch(batch: BatchCreate, session: Session = Depends(get_session)):
    return crud.create_batch(session, batch.dict())

@router.get("/batches/", response_model=List[BatchRead])
def list_batches(session: Session = Depends(get_session)):
    return crud.list_batches(session)

@router.get("/batches/{batch_id}", response_model=BatchRead)
def get_batch(batch_id: int, session: Session = Depends(get_session)):
    batch = crud.get_batch(session, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch

@router.put("/batches/{batch_id}", response_model=BatchRead)
def update_batch(batch_id: int, batch: BatchCreate, session: Session = Depends(get_session)):
    db_batch = crud.get_batch(session, batch_id)
    if not db_batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return crud.update_batch(session, db_batch, batch.dict(exclude_unset=True))

@router.delete("/batches/{batch_id}")
def delete_batch(batch_id: int, session: Session = Depends(get_session)):
    db_batch = crud.get_batch(session, batch_id)
    if not db_batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    crud.delete_batch(session, db_batch)
    return {"ok": True}

# --- Project Endpoints ---
@router.post("/projects/", response_model=ProjectRead)
def create_project(project: ProjectCreate, session: Session = Depends(get_session)):
    return crud.create_project(session, project.dict())

@router.get("/projects/", response_model=List[ProjectRead])
def list_projects(session: Session = Depends(get_session)):
    return crud.list_projects(session)

@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_session)):
    project = crud.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/projects/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, project: ProjectCreate, session: Session = Depends(get_session)):
    db_project = crud.get_project(session, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.update_project(session, db_project, project.dict(exclude_unset=True))

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, session: Session = Depends(get_session)):
    db_project = crud.get_project(session, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    crud.delete_project(session, db_project)
    return {"ok": True}

# --- Student Endpoints ---
@router.post("/students/", response_model=StudentRead)
def create_student(student: StudentCreate, session: Session = Depends(get_session)):
    return crud.create_student(session, student.dict())

@router.get("/students/", response_model=List[StudentRead])
def list_students(session: Session = Depends(get_session)):
    return crud.list_students(session)

@router.get("/students/{student_id}", response_model=StudentRead)
def get_student(student_id: int, session: Session = Depends(get_session)):
    student = crud.get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/students/{student_id}", response_model=StudentRead)
def update_student(student_id: int, student: StudentCreate, session: Session = Depends(get_session)):
    db_student = crud.get_student(session, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return crud.update_student(session, db_student, student.dict(exclude_unset=True))

@router.delete("/students/{student_id}")
def delete_student(student_id: int, session: Session = Depends(get_session)):
    db_student = crud.get_student(session, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    crud.delete_student(session, db_student)
    return {"ok": True}

# --- Certificate Endpoints ---
@router.get("/students/{student_id}/certificates", response_model=List[CertificateRead])
def list_certificates(student_id: int, session: Session = Depends(get_session)):
    return crud.get_certificates_by_student(session, student_id)

@router.post("/students/{student_id}/certificates", response_model=CertificateRead)
def create_certificate(student_id: int, cert: CertificateCreate, session: Session = Depends(get_session)):
    return crud.create_certificate(session, student_id, cert.dict())

@router.put("/students/{student_id}/certificates/{certificate_id}", response_model=CertificateRead)
def update_certificate(student_id: int, certificate_id: int, cert: CertificateUpdate, session: Session = Depends(get_session)):
    db_cert = crud.get_certificate(session, certificate_id)
    if not db_cert or db_cert.student_id != student_id:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return crud.update_certificate(session, db_cert, cert.dict(exclude_unset=True))

@router.delete("/students/{student_id}/certificates/{certificate_id}")
def delete_certificate(student_id: int, certificate_id: int, session: Session = Depends(get_session)):
    db_cert = crud.get_certificate(session, certificate_id)
    if not db_cert or db_cert.student_id != student_id:
        raise HTTPException(status_code=404, detail="Certificate not found")
    crud.delete_certificate(session, db_cert)
    return {"ok": True}

# --- Demo Endpoints ---
@router.get("/students/{student_id}/demos", response_model=List[DemoRead])
def list_demos(student_id: int, session: Session = Depends(get_session)):
    return crud.get_demos_by_student(session, student_id)

@router.post("/students/{student_id}/demos", response_model=DemoRead)
def create_demo(student_id: int, demo: DemoCreate, session: Session = Depends(get_session)):
    return crud.create_demo(session, student_id, demo.dict())

@router.put("/students/{student_id}/demos/{demo_id}", response_model=DemoRead)
def update_demo(student_id: int, demo_id: int, demo: DemoUpdate, session: Session = Depends(get_session)):
    db_demo = crud.get_demo(session, demo_id)
    if not db_demo or db_demo.student_id != student_id:
        raise HTTPException(status_code=404, detail="Demo not found")
    return crud.update_demo(session, db_demo, demo.dict(exclude_unset=True))

@router.delete("/students/{student_id}/demos/{demo_id}")
def delete_demo(student_id: int, demo_id: int, session: Session = Depends(get_session)):
    db_demo = crud.get_demo(session, demo_id)
    if not db_demo or db_demo.student_id != student_id:
        raise HTTPException(status_code=404, detail="Demo not found")
    crud.delete_demo(session, db_demo)
    return {"ok": True} 