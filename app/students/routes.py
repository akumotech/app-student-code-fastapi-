from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from typing import List
from .models import Student, Certificate, Demo
from app.students.schemas import (
    StudentCreate, StudentRead,
    CertificateCreate, CertificateUpdate, CertificateRead,
    DemoCreate, DemoUpdate, DemoRead
)
from app.auth.database import engine

router = APIRouter()

def get_session():
    with Session(engine) as session:
        yield session

# --- Certificate Endpoints ---
@router.get("/students/{student_id}/certificates", response_model=List[CertificateRead])
def list_certificates(student_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Certificate).where(Certificate.student_id == student_id)).all()

@router.post("/students/{student_id}/certificates", response_model=CertificateRead)
def create_certificate(student_id: int, cert: CertificateCreate, session: Session = Depends(get_session)):
    db_cert = Certificate(**cert.dict(), student_id=student_id)
    session.add(db_cert)
    session.commit()
    session.refresh(db_cert)
    return db_cert

@router.put("/students/{student_id}/certificates/{certificate_id}", response_model=CertificateRead)
def update_certificate(student_id: int, certificate_id: int, cert: CertificateUpdate, session: Session = Depends(get_session)):
    db_cert = session.get(Certificate, certificate_id)
    if not db_cert or db_cert.student_id != student_id:
        raise HTTPException(status_code=404, detail="Certificate not found")
    for key, value in cert.dict(exclude_unset=True).items():
        setattr(db_cert, key, value)
    session.add(db_cert)
    session.commit()
    session.refresh(db_cert)
    return db_cert

@router.delete("/students/{student_id}/certificates/{certificate_id}")
def delete_certificate(student_id: int, certificate_id: int, session: Session = Depends(get_session)):
    db_cert = session.get(Certificate, certificate_id)
    if not db_cert or db_cert.student_id != student_id:
        raise HTTPException(status_code=404, detail="Certificate not found")
    session.delete(db_cert)
    session.commit()
    return {"ok": True}

# --- Demo Endpoints ---
@router.get("/students/{student_id}/demos", response_model=List[DemoRead])
def list_demos(student_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Demo).where(Demo.student_id == student_id)).all()

@router.post("/students/{student_id}/demos", response_model=DemoRead)
def create_demo(student_id: int, demo: DemoCreate, session: Session = Depends(get_session)):
    db_demo = Demo(**demo.dict(), student_id=student_id)
    session.add(db_demo)
    session.commit()
    session.refresh(db_demo)
    return db_demo

@router.put("/students/{student_id}/demos/{demo_id}", response_model=DemoRead)
def update_demo(student_id: int, demo_id: int, demo: DemoUpdate, session: Session = Depends(get_session)):
    db_demo = session.get(Demo, demo_id)
    if not db_demo or db_demo.student_id != student_id:
        raise HTTPException(status_code=404, detail="Demo not found")
    for key, value in demo.dict(exclude_unset=True).items():
        setattr(db_demo, key, value)
    session.add(db_demo)
    session.commit()
    session.refresh(db_demo)
    return db_demo

@router.delete("/students/{student_id}/demos/{demo_id}")
def delete_demo(student_id: int, demo_id: int, session: Session = Depends(get_session)):
    db_demo = session.get(Demo, demo_id)
    if not db_demo or db_demo.student_id != student_id:
        raise HTTPException(status_code=404, detail="Demo not found")
    session.delete(db_demo)
    session.commit()
    return {"ok": True} 