from sqlmodel import Session, select
from .models import Certificates, Demos, Batches, Projects, Students
from typing import List, Optional

def get_certificates_by_student(session: Session, student_id: int) -> List[Certificates]:
    return session.exec(select(Certificates).where(Certificates.student_id == student_id)).all()

def get_certificate(session: Session, certificate_id: int) -> Optional[Certificates]:
    return session.get(Certificates, certificate_id)

def create_certificate(session: Session, student_id: int, cert_data: dict) -> Certificates:
    cert = Certificates(**cert_data, student_id=student_id)
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return cert

def update_certificate(session: Session, db_cert: Certificates, update_data: dict) -> Certificates:
    for key, value in update_data.items():
        setattr(db_cert, key, value)
    session.add(db_cert)
    session.commit()
    session.refresh(db_cert)
    return db_cert

def delete_certificate(session: Session, db_cert: Certificates):
    session.delete(db_cert)
    session.commit()

def get_demos_by_student(session: Session, student_id: int) -> List[Demos]:
    return session.exec(select(Demos).where(Demos.student_id == student_id)).all()

def get_demo(session: Session, demo_id: int) -> Optional[Demos]:
    return session.get(Demo, demo_id)

def create_demo(session: Session, student_id: int, demo_data: dict) -> Demos:
    demo = Demos(**demo_data, student_id=student_id)
    session.add(demo)
    session.commit()
    session.refresh(demo)
    return demo

def update_demo(session: Session, db_demo: Demos, update_data: dict) -> Demos:
    for key, value in update_data.items():
        setattr(db_demo, key, value)
    session.add(db_demo)
    session.commit()
    session.refresh(db_demo)
    return db_demo

def delete_demo(session: Session, db_demo: Demos):
    session.delete(db_demo)
    session.commit()

# --- Batch CRUD ---
def create_batch(session: Session, batch_data: dict) -> Batches:
    batch = Batches(**batch_data)
    session.add(batch)
    session.commit()
    session.refresh(batch)
    return batch

def get_batch(session: Session, batch_id: int) -> Optional[Batches]:
    return session.get(Batches, batch_id)

def list_batches(session: Session) -> List[Batches]:
    return session.exec(select(Batches)).all()

def update_batch(session: Session, db_batch: Batches, update_data: dict) -> Batches:
    for key, value in update_data.items():
        setattr(db_batch, key, value)
    session.add(db_batch)
    session.commit()
    session.refresh(db_batch)
    return db_batch

def delete_batch(session: Session, db_batch: Batches):
    session.delete(db_batch)
    session.commit()

# --- Project CRUD ---
def create_project(session: Session, project_data: dict) -> Projects:
    projects = Projects(**project_data)
    session.add(project)
    session.commit()
    session.refresh(project)
    return projects

def get_project(session: Session, project_id: int) -> Optional[Projects]:
    return session.get(Projects, project_id)

def list_projects(session: Session) -> List[Projects]:
    return session.exec(select(Projects)).all()

def update_project(session: Session, db_project: Projects, update_data: dict) -> Projects:
    for key, value in update_data.items():
        setattr(db_project, key, value)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

def delete_project(session: Session, db_project: Projects):
    session.delete(db_project)
    session.commit()

# --- Student CRUD ---
def create_student(session: Session, student_data: dict) -> Students:
    student = Students(**student_data)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student

def get_student(session: Session, student_id: int) -> Optional[Students]:
    return session.get(Students, student_id)

def list_students(session: Session) -> List[Students]:
    return session.exec(select(Students)).all()

def update_student(session: Session, db_student: Students, update_data: dict) -> Students:
    for key, value in update_data.items():
        setattr(db_student, key, value)
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student

def delete_student(session: Session, db_student: Students):
    session.delete(db_student)
    session.commit() 