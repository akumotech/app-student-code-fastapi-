from sqlmodel import Session, select
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import func, and_, or_

# Assuming singular model and schema names
from .models import Student, Certificate, Demo, Batch, Project, DemoSession, DemoSignup
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
    DemoSessionCreate,
    DemoSessionUpdate,
    DemoSignupCreate,
    DemoSignupUpdate,
    DemoSignupAdminUpdate,
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


def get_students_by_batch(session: Session, batch_id: int) -> List[Student]:
    return session.exec(select(Student).where(Student.batch_id == batch_id)).all()


# --- Demo Session CRUD ---
def get_demo_sessions(
    session: Session, 
    include_inactive: bool = False,
    include_cancelled: bool = False
) -> List[DemoSession]:
    """Get demo sessions with optional filtering"""
    query = select(DemoSession)
    
    if not include_inactive:
        query = query.where(DemoSession.is_active == True)
    
    if not include_cancelled:
        query = query.where(DemoSession.is_cancelled == False)
    
    query = query.order_by(DemoSession.session_date.desc())
    return session.exec(query).all()


def get_demo_session(session: Session, session_id: int) -> Optional[DemoSession]:
    """Get a single demo session by ID"""
    return session.get(DemoSession, session_id)


def get_demo_session_by_date(
    session: Session, session_date: date
) -> Optional[DemoSession]:
    """Get demo session by date"""
    query = select(DemoSession).where(DemoSession.session_date == session_date)
    return session.exec(query).first()


def create_demo_session(
    session: Session, demo_session_create: DemoSessionCreate
) -> DemoSession:
    """Create a new demo session"""
    demo_session = DemoSession(**demo_session_create.dict())
    session.add(demo_session)
    session.flush()
    return demo_session


def update_demo_session(
    session: Session, db_session: DemoSession, session_update: DemoSessionUpdate
) -> DemoSession:
    """Update an existing demo session"""
    update_data = session_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(db_session, key, value)
    
    session.add(db_session)
    session.flush()
    return db_session


def delete_demo_session(session: Session, db_session: DemoSession) -> None:
    """Delete a demo session and all its signups"""
    session.delete(db_session)
    session.flush()


def get_demo_sessions_with_signup_counts(
    session: Session, 
    student_id: Optional[int] = None,
    batch_id: Optional[int] = None  # For filtering by student's batch
) -> List[tuple]:
    """Get demo sessions with signup counts and user signup status"""
    query = select(
        DemoSession,
        func.count(DemoSignup.id).label("signup_count")
    ).outerjoin(DemoSignup)
    
    # If batch_id is provided, filter by students from that batch
    if batch_id:
        from app.students.models import Student
        query = query.outerjoin(Student, DemoSignup.student_id == Student.id).where(
            or_(Student.batch_id == batch_id, DemoSignup.id.is_(None))
        )
    
    query = query.group_by(DemoSession.id).order_by(DemoSession.session_date.desc())
    
    results = session.exec(query).all()
    
    # If student_id provided, check if they're scheduled for each session
    if student_id:
        session_ids = [demo_session.id for demo_session, _ in results]
        scheduled_sessions = session.exec(
            select(DemoSignup.session_id).where(
                and_(
                    DemoSignup.session_id.in_(session_ids),
                    DemoSignup.student_id == student_id
                )
            )
        ).all()
        scheduled_set = set(scheduled_sessions)
        
        return [(demo_session, count, demo_session.id in scheduled_set) for demo_session, count in results]
    
    return [(demo_session, count, False) for demo_session, count in results]


# --- Demo Signup CRUD ---
def get_demo_signups_by_session(
    session: Session, session_id: int
) -> List[dict]:
    """Get all signups for a specific demo session with student user details"""
    from app.auth.models import User
    
    # Use a join query to get signup, student, and user data in one query
    query = (
        select(
            DemoSignup,
            Student,
            User.name,
            User.email
        )
        .join(Student, DemoSignup.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .where(DemoSignup.session_id == session_id)
        .order_by(DemoSignup.scheduled_at.desc())
    )
    
    results = session.exec(query).all()
    
    # Convert results to dict format with enhanced student data
    signups = []
    for signup, student_data, user_name, user_email in results:
        # Create a dict representation for the enhanced student data
        enhanced_student = {
            "id": student_data.id,
            "user_id": student_data.user_id,
            "name": user_name,
            "email": user_email
        }
        
        # Convert signup to dict and add enhanced student data
        signup_dict = signup.__dict__.copy()
        signup_dict["student"] = enhanced_student
        
        # Load demo if exists
        if signup.demo_id:
            demo = session.get(Demo, signup.demo_id)
            signup_dict["demo"] = demo.__dict__ if demo else None
        else:
            signup_dict["demo"] = None
        
        signups.append(signup_dict)
    
    return signups


def get_demo_signups_by_student(
    session: Session, student_id: int
) -> List[dict]:
    """Get all demo signups by a student with student user details"""
    from app.auth.models import User
    
    # Use a join query to get signup, student, and user data
    query = (
        select(
            DemoSignup,
            Student,
            User.name,
            User.email
        )
        .join(Student, DemoSignup.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .where(DemoSignup.student_id == student_id)
        .order_by(DemoSignup.scheduled_at.desc())
    )
    
    results = session.exec(query).all()
    
    # Convert results to dict format with enhanced student data
    signups = []
    for signup, student_data, user_name, user_email in results:
        # Create a dict representation for the enhanced student data
        enhanced_student = {
            "id": student_data.id,
            "user_id": student_data.user_id,
            "name": user_name,
            "email": user_email
        }
        
        # Convert signup to dict and add enhanced student data
        signup_dict = signup.__dict__.copy()
        signup_dict["student"] = enhanced_student
        
        # Load demo if exists
        if signup.demo_id:
            demo = session.get(Demo, signup.demo_id)
            signup_dict["demo"] = demo.__dict__ if demo else None
        else:
            signup_dict["demo"] = None
        
        signups.append(signup_dict)
    
    return signups


def get_demo_signup(session: Session, signup_id: int) -> Optional[DemoSignup]:
    """Get a single demo signup by ID"""
    return session.get(DemoSignup, signup_id)


def get_demo_signup_enhanced(session: Session, signup_id: int) -> Optional[dict]:
    """Get a single demo signup with enhanced student data (name, email)"""
    from app.auth.models import User
    
    query = (
        select(
            DemoSignup,
            Student,
            User.name,
            User.email
        )
        .join(Student, DemoSignup.student_id == Student.id)
        .join(User, Student.user_id == User.id)
        .where(DemoSignup.id == signup_id)
    )
    
    result = session.exec(query).first()
    if not result:
        return None
    
    signup, student_data, user_name, user_email = result
    
    # Create a dict representation for the enhanced student data
    enhanced_student = {
        "id": student_data.id,
        "user_id": student_data.user_id,
        "name": user_name,
        "email": user_email
    }
    
    # Convert signup to dict and add enhanced student data
    signup_dict = signup.__dict__.copy()
    signup_dict["student"] = enhanced_student
    
    # Load demo if exists
    if signup.demo_id:
        demo = session.get(Demo, signup.demo_id)
        signup_dict["demo"] = demo.__dict__ if demo else None
    else:
        signup_dict["demo"] = None
    
    return signup_dict


def get_demo_signup_by_session_and_student(
    session: Session, session_id: int, student_id: int
) -> Optional[DemoSignup]:
    """Check if student is already signed up for this session"""
    query = select(DemoSignup).where(
        and_(
            DemoSignup.session_id == session_id,
            DemoSignup.student_id == student_id
        )
    )
    return session.exec(query).first()


def create_demo_signup(
    session: Session, 
    session_id: int,
    student_id: int,
    signup_create: DemoSignupCreate
) -> DemoSignup:
    """Create a new demo signup"""
    signup_data = signup_create.dict()
    signup_data.update({
        "session_id": session_id,
        "student_id": student_id
    })
    
    demo_signup = DemoSignup(**signup_data)
    session.add(demo_signup)
    session.flush()
    return demo_signup


def update_demo_signup(
    session: Session, 
    db_signup: DemoSignup, 
    signup_update: DemoSignupUpdate
) -> DemoSignup:
    """Update a demo signup (student perspective)"""
    update_data = signup_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(db_signup, key, value)
    
    session.add(db_signup)
    session.flush()
    return db_signup


def update_demo_signup_admin(
    session: Session,
    db_signup: DemoSignup,
    admin_update: DemoSignupAdminUpdate
) -> DemoSignup:
    """Update a demo signup (admin perspective - after presentation)"""
    update_data = admin_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(db_signup, key, value)
    
    session.add(db_signup)
    session.flush()
    return db_signup


def delete_demo_signup(session: Session, db_signup: DemoSignup) -> None:
    """Delete/cancel a demo signup"""
    session.delete(db_signup)
    session.flush()


def check_session_signup_limit(session: Session, session_id: int) -> tuple[int, Optional[int]]:
    """Check current signup count vs max limit for a session"""
    demo_session = session.get(DemoSession, session_id)
    if not demo_session:
        return 0, None
    
    current_count = session.exec(
        select(func.count(DemoSignup.id)).where(DemoSignup.session_id == session_id)
    ).first()
    
    return current_count or 0, demo_session.max_scheduled
