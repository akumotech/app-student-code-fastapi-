from sqlmodel import Session, select
from typing import List, Optional

# Assuming singular model and schema names
from .models import Student, Certificate, Demo, Batch, Project
from .schemas import (
    StudentCreate,
    StudentUpdate,  # Assuming StudentUpdate exists or is same as StudentCreate for now
    CertificateCreate,
    CertificateUpdate,
    DemoCreate,
    DemoUpdate,
    BatchCreate,
    BatchUpdate,  # Assuming BatchUpdate exists
    ProjectCreate,
    ProjectUpdate,  # Assuming ProjectUpdate exists
)


# --- Student CRUD ---
def get_student(session: Session, student_id: int) -> Optional[Student]:
    return session.get(Student, student_id)


def get_student_by_user_id(session: Session, user_id: int) -> Optional[Student]:
    return session.exec(select(Student).where(Student.user_id == user_id)).first()


def list_students(session: Session) -> List[Student]:
    return session.exec(select(Student)).all()


def create_student(session: Session, student_create: StudentCreate) -> Student:
    # Note: Student creation is also in auth.py's /students/register.
    # This CRUD function is for a more generic student creation if needed elsewhere.
    # Ensure student_create schema has all necessary fields (e.g. user_id).
    student = Student.from_orm(student_create)  # SQLModel/Pydantic v2 way
    session.add(student)
    session.flush()
    return student


def update_student(
    session: Session, db_student: Student, student_update: StudentUpdate
) -> Student:
    update_data = student_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    session.add(db_student)
    session.flush()
    return db_student


def delete_student(session: Session, db_student: Student) -> None:
    session.delete(db_student)
    session.flush()


# --- Certificate CRUD ---
def get_certificates_by_student(session: Session, student_id: int) -> List[Certificate]:
    return session.exec(
        select(Certificate).where(Certificate.student_id == student_id)
    ).all()


def get_certificate(session: Session, certificate_id: int) -> Optional[Certificate]:
    return session.get(Certificate, certificate_id)


def create_certificate(
    session: Session, student_id: int, cert_create: CertificateCreate
) -> Certificate:
    cert = Certificate(**cert_create.dict(), student_id=student_id)
    session.add(cert)
    session.flush()
    return cert


def update_certificate(
    session: Session, db_cert: Certificate, cert_update: CertificateUpdate
) -> Certificate:
    update_data = cert_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cert, key, value)
    session.add(db_cert)
    session.flush()
    return db_cert


def delete_certificate(session: Session, db_cert: Certificate) -> None:
    session.delete(db_cert)
    session.flush()


# --- Demo CRUD ---
def get_demos_by_student(session: Session, student_id: int) -> List[Demo]:
    return session.exec(select(Demo).where(Demo.student_id == student_id)).all()


def get_demo(session: Session, demo_id: int) -> Optional[Demo]:
    return session.get(Demo, demo_id)


def create_demo(session: Session, student_id: int, demo_create: DemoCreate) -> Demo:
    demo = Demo(**demo_create.dict(), student_id=student_id)
    session.add(demo)
    session.flush()
    return demo


def update_demo(session: Session, db_demo: Demo, demo_update: DemoUpdate) -> Demo:
    update_data = demo_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_demo, key, value)
    session.add(db_demo)
    session.flush()
    return db_demo


def delete_demo(session: Session, db_demo: Demo) -> None:
    session.delete(db_demo)
    session.flush()


# --- Batch CRUD ---
def get_batch(session: Session, batch_id: int) -> Optional[Batch]:
    return session.get(Batch, batch_id)


def list_batches(session: Session) -> List[Batch]:
    return session.exec(select(Batch)).all()


def create_batch(session: Session, batch_create: BatchCreate) -> Batch:
    batch = Batch.from_orm(batch_create)
    session.add(batch)
    session.flush()
    return batch


def update_batch(session: Session, db_batch: Batch, batch_update: BatchUpdate) -> Batch:
    update_data = batch_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_batch, key, value)
    session.add(db_batch)
    session.flush()
    return db_batch


def delete_batch(session: Session, db_batch: Batch) -> None:
    session.delete(db_batch)
    session.flush()


# --- Project CRUD ---
def get_project(session: Session, project_id: int) -> Optional[Project]:
    return session.get(Project, project_id)


def list_projects(session: Session) -> List[Project]:
    return session.exec(select(Project)).all()


def create_project(session: Session, project_create: ProjectCreate) -> Project:
    project = Project.from_orm(project_create)
    session.add(project)
    session.flush()
    return project


def update_project(
    session: Session, db_project: Project, project_update: ProjectUpdate
) -> Project:
    update_data = project_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    session.add(db_project)
    session.flush()
    return db_project


def delete_project(session: Session, db_project: Project) -> None:
    session.delete(db_project)
    session.flush()
