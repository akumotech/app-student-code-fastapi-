from sqlmodel import Session, select
from .models import Certificate, Demo
from typing import List, Optional

def get_certificates_by_student(session: Session, student_id: int) -> List[Certificate]:
    return session.exec(select(Certificate).where(Certificate.student_id == student_id)).all()

def get_certificate(session: Session, certificate_id: int) -> Optional[Certificate]:
    return session.get(Certificate, certificate_id)

def create_certificate(session: Session, student_id: int, cert_data: dict) -> Certificate:
    cert = Certificate(**cert_data, student_id=student_id)
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return cert

def update_certificate(session: Session, db_cert: Certificate, update_data: dict) -> Certificate:
    for key, value in update_data.items():
        setattr(db_cert, key, value)
    session.add(db_cert)
    session.commit()
    session.refresh(db_cert)
    return db_cert

def delete_certificate(session: Session, db_cert: Certificate):
    session.delete(db_cert)
    session.commit()

def get_demos_by_student(session: Session, student_id: int) -> List[Demo]:
    return session.exec(select(Demo).where(Demo.student_id == student_id)).all()

def get_demo(session: Session, demo_id: int) -> Optional[Demo]:
    return session.get(Demo, demo_id)

def create_demo(session: Session, student_id: int, demo_data: dict) -> Demo:
    demo = Demo(**demo_data, student_id=student_id)
    session.add(demo)
    session.commit()
    session.refresh(demo)
    return demo

def update_demo(session: Session, db_demo: Demo, update_data: dict) -> Demo:
    for key, value in update_data.items():
        setattr(db_demo, key, value)
    session.add(db_demo)
    session.commit()
    session.refresh(db_demo)
    return db_demo

def delete_demo(session: Session, db_demo: Demo):
    session.delete(db_demo)
    session.commit() 