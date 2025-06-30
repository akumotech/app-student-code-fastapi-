from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
from sqlmodel import Session
from typing import List

from . import crud
from .models import (
    Student,
)  # Only Student needed directly for type hints if any, crud handles others
from .schemas import (
    StudentCreate,
    StudentRead,
    StudentUpdate,  # Added StudentUpdate
    CertificateCreate,
    CertificateUpdate,
    CertificateRead,
    DemoCreate,
    DemoUpdate,
    DemoRead,
    BatchCreate,
    BatchRead,
    BatchUpdate,  # Added BatchUpdate
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,  # Added ProjectUpdate
    DemoSessionSummary,
    DemoSignupCreate,
    DemoSignupRead,
    DemoSignupUpdate,
)

from app.auth.database import get_session
from app.auth.utils import get_current_active_user
from app.auth.schemas import User as UserSchema  # For current_user type hint
from app.auth.auth import APIResponse  # Import the standardized APIResponse

router = APIRouter()


# --- Authorization Helper Functions (Generalized) ---
def get_authorized_student_for_action(
    student_id: int,
    current_user: UserSchema,
    session: Session,
    allow_owner: bool = True,
):
    """Checks if current_user can act on behalf of student_id."""
    db_student = crud.get_student(session, student_id)
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found",
        )

    is_owner = current_user.id == db_student.user_id
    is_admin_or_instructor = current_user.role in ["admin", "instructor"]

    if is_admin_or_instructor:
        return db_student
    if allow_owner and is_owner:
        return db_student

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized for this student-related action",
    )


def require_roles(current_user: UserSchema, allowed_roles: List[str]):
    """Ensures current_user has one of the allowed_roles."""
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Action requires one of roles: {allowed_roles}",
        )


# --- Batch Endpoints ---
@router.post(
    "/batches/", response_model=BatchRead, summary="Create Batch", tags=["Batches"]
)
def create_batch_endpoint(
    batch_data: BatchCreate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    batch = crud.create_batch(session, batch_create=batch_data)
    session.commit()
    session.refresh(batch)
    return batch


@router.get(
    "/batches/",
    response_model=List[BatchRead],
    summary="List Batches",
    tags=["Batches"],
)
def list_batches_endpoint(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    # All authenticated users can list batches
    return crud.list_batches(session)


@router.get(
    "/batches/{batch_id}",
    response_model=BatchRead,
    summary="Get Batch by ID",
    tags=["Batches"],
)
def get_batch_endpoint(
    batch_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    db_batch = crud.get_batch(session, batch_id)
    if not db_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found"
        )
    return db_batch


@router.put(
    "/batches/{batch_id}",
    response_model=BatchRead,
    summary="Update Batch",
    tags=["Batches"],
)
def update_batch_endpoint(
    batch_id: int,
    batch_data: BatchUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    db_batch = crud.get_batch(session, batch_id)
    if not db_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found"
        )
    updated_batch = crud.update_batch(
        session, db_batch=db_batch, batch_update=batch_data
    )
    session.commit()
    session.refresh(updated_batch)
    return updated_batch


@router.delete(
    "/batches/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Batch",
    tags=["Batches"],
)
def delete_batch_endpoint(
    batch_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    db_batch = crud.get_batch(session, batch_id)
    if not db_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found"
        )
    crud.delete_batch(session, db_batch=db_batch)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/batches/{batch_id}/students",
    response_model=List[StudentRead],
    summary="List Students in a Batch",
    tags=["Batches", "Students"],
)
def list_students_in_batch(
    batch_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    return crud.get_students_by_batch(session, batch_id)


# --- Project Endpoints ---
@router.post(
    "/projects/",
    response_model=ProjectRead,
    summary="Create Project",
    tags=["Projects"],
)
def create_project_endpoint(
    project_data: ProjectCreate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    project = crud.create_project(session, project_create=project_data)
    session.commit()
    session.refresh(project)
    return project


@router.get(
    "/projects/",
    response_model=List[ProjectRead],
    summary="List Projects",
    tags=["Projects"],
)
def list_projects_endpoint(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    return crud.list_projects(session)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectRead,
    summary="Get Project by ID",
    tags=["Projects"],
)
def get_project_endpoint(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    db_project = crud.get_project(session, project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return db_project


@router.put(
    "/projects/{project_id}",
    response_model=ProjectRead,
    summary="Update Project",
    tags=["Projects"],
)
def update_project_endpoint(
    project_id: int,
    project_data: ProjectUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    db_project = crud.get_project(session, project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    updated_project = crud.update_project(
        session, db_project=db_project, project_update=project_data
    )
    session.commit()
    session.refresh(updated_project)
    return updated_project


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Project",
    tags=["Projects"],
)
def delete_project_endpoint(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    db_project = crud.get_project(session, project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    crud.delete_project(session, db_project=db_project)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Student Profile Endpoints (distinct from auth-related student registration) ---
# These allow managing student profiles if needed, separate from auth /students/register
@router.get(
    "/students/",
    response_model=List[StudentRead],
    summary="List Students",
    tags=["Students"],
)
def list_students_endpoint(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_roles(current_user, ["admin", "instructor"])
    return crud.list_students(session)


@router.get(
    "/students/{student_id}",
    response_model=StudentRead,
    summary="Get Student by ID",
    tags=["Students"],
)
def get_student_endpoint(
    student_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    # Admins/instructors can get any student. Student can get their own profile.
    db_student = crud.get_student(session, student_id)
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found",
        )

    if (
        current_user.role not in ["admin", "instructor"]
        and current_user.id != db_student.user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this student profile",
        )
    return db_student


@router.put(
    "/students/{student_id}",
    response_model=StudentRead,
    summary="Update Student Profile",
    tags=["Students"],
)
def update_student_endpoint(
    student_id: int,
    student_data: StudentUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    # Admins/instructors can update any student. Student can update their own profile.
    db_student = get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )
    updated_student = crud.update_student(
        session, db_student=db_student, student_update=student_data
    )
    session.commit()
    session.refresh(updated_student)
    return updated_student


# Note: Student creation is via /auth/students/register. Deletion might be complex (cascade, archiving).
# @router.delete("/students/{student_id}", ...)

# --- "Me" Endpoints for Logged-in Student ---


@router.get(
    "/students/me/certificates",
    response_model=List[CertificateRead],
    summary="List My Certificates",
    tags=["My Student Data"],
)
def list_my_certificates(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "student" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not a student"
        )

    db_student = (
        session.query(Student).filter(Student.user_id == current_user.id).first()
    )

    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for current user.",
        )

    return crud.get_certificates_by_student(session, student_id=db_student.id)


@router.get(
    "/students/me/demos",
    response_model=List[DemoRead],
    summary="List My Demos",
    tags=["My Student Data"],
)
def list_my_demos(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    if current_user.role != "student" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not a student"
        )

    db_student = (
        session.query(Student).filter(Student.user_id == current_user.id).first()
    )
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found for current user.",
        )

    return crud.get_demos_by_student(session, student_id=db_student.id)


# --- Certificate Endpoints (Scoped to a Student) ---
@router.get(
    "/students/{student_id}/certificates",
    response_model=List[CertificateRead],
    summary="List Student Certificates",
    tags=["Student Specific"],
)
def list_student_certificates(
    student_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )  # Read access for owner or admin/instructor
    return crud.get_certificates_by_student(session, student_id=student_id)


@router.post(
    "/students/{student_id}/certificates",
    response_model=CertificateRead,
    summary="Create Student Certificate",
    tags=["Student Specific"],
)
def create_student_certificate(
    student_id: int,
    cert_schema: CertificateCreate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )  # Write access for owner or admin/instructor
    certificate = crud.create_certificate(
        session, student_id=student_id, cert_create=cert_schema
    )
    session.commit()
    session.refresh(certificate)
    return certificate


@router.put(
    "/students/{student_id}/certificates/{certificate_id}",
    response_model=CertificateRead,
    summary="Update Student Certificate",
    tags=["Student Specific"],
)
def update_student_certificate(
    student_id: int,
    certificate_id: int,
    cert_schema: CertificateUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )
    db_cert = crud.get_certificate(session, certificate_id=certificate_id)
    if (
        not db_cert or db_cert.student_id != student_id
    ):  # Ensure certificate belongs to the student path
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found or does not belong to this student",
        )
    updated_cert = crud.update_certificate(
        session, db_cert=db_cert, cert_update=cert_schema
    )
    session.commit()
    session.refresh(updated_cert)
    return updated_cert


@router.delete(
    "/students/{student_id}/certificates/{certificate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Student Certificate",
    tags=["Student Specific"],
)
def delete_student_certificate(
    student_id: int,
    certificate_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )
    db_cert = crud.get_certificate(session, certificate_id=certificate_id)
    if not db_cert or db_cert.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found or does not belong to this student",
        )
    crud.delete_certificate(session, db_cert=db_cert)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Demo Endpoints (Scoped to a Student) ---
@router.get(
    "/students/{student_id}/demos",
    response_model=List[DemoRead],
    summary="List Student Demos",
    tags=["Student Specific"],
)
def list_student_demos(
    student_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )
    return crud.get_demos_by_student(session, student_id=student_id)


@router.post(
    "/students/{student_id}/demos",
    response_model=DemoRead,
    summary="Create Student Demo",
    tags=["Student Specific"],
)
def create_student_demo(
    student_id: int,
    demo_schema: DemoCreate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )
    demo = crud.create_demo(session, student_id=student_id, demo_create=demo_schema)
    session.commit()
    session.refresh(demo)
    return demo


@router.put(
    "/students/{student_id}/demos/{demo_id}",
    response_model=DemoRead,
    summary="Update Student Demo",
    tags=["Student Specific"],
)
def update_student_demo(
    student_id: int,
    demo_id: int,
    demo_schema: DemoUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )
    db_demo = crud.get_demo(session, demo_id=demo_id)
    if not db_demo or db_demo.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found or does not belong to this student",
        )
    updated_demo = crud.update_demo(session, db_demo=db_demo, demo_update=demo_schema)
    session.commit()
    session.refresh(updated_demo)
    return updated_demo


@router.delete(
    "/students/{student_id}/demos/{demo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Student Demo",
    tags=["Student Specific"],
)
def delete_student_demo(
    student_id: int,
    demo_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    get_authorized_student_for_action(
        student_id, current_user, session, allow_owner=True
    )
    db_demo = crud.get_demo(session, demo_id=demo_id)
    if not db_demo or db_demo.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found or does not belong to this student",
        )
    crud.delete_demo(session, db_demo=db_demo)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Demo Session Endpoints (Student) ---
@router.get(
    "/demo-sessions",
    response_model=List[DemoSessionSummary],
    summary="List Available Demo Sessions",
    tags=["Demo Sessions"],
)
def list_available_demo_sessions(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    """List available demo sessions for the current student"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only students can view demo sessions"
        )
    
    # Get student info
    db_student = session.query(Student).filter(Student.user_id == current_user.id).first()
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Get sessions with signup counts and user signup status
    sessions_data = crud.get_demo_sessions_with_signup_counts(
        session, student_id=db_student.id, batch_id=db_student.batch_id
    )
    
    result = []
    for demo_session, signup_count, user_scheduled in sessions_data:
        # Only show active, non-cancelled sessions
        if demo_session.is_active and not demo_session.is_cancelled:
            session_summary = DemoSessionSummary(
                id=demo_session.id,
                session_date=demo_session.session_date,
                is_active=demo_session.is_active,
                is_cancelled=demo_session.is_cancelled,
                max_scheduled=demo_session.max_scheduled,
                title=demo_session.title,
                signup_count=signup_count,
                user_scheduled=user_scheduled
            )
            result.append(session_summary)
    
    return result


@router.post(
    "/demo-sessions/{session_id}/signup",
    response_model=DemoSignupRead,
    summary="Sign Up for Demo Session",
    tags=["Demo Sessions"],
)
def signup_for_demo_session(
    session_id: int,
    signup_data: DemoSignupCreate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    """Sign up for a demo session"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can sign up for demo sessions"
        )
    
    # Get student info
    db_student = session.query(Student).filter(Student.user_id == current_user.id).first()
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Get demo session
    demo_session = crud.get_demo_session(session, session_id)
    if not demo_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found"
        )
    
    # Validation checks
    if not demo_session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This demo session is not accepting signups"
        )
    
    if demo_session.is_cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This demo session has been cancelled"
        )
    
    # Note: Since demo sessions are not tied to batches directly,
    # students from any batch can sign up for any active session
    
    # Check if already signed up
    existing_signup = crud.get_demo_signup_by_session_and_student(
        session, session_id, db_student.id
    )
    if existing_signup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already signed up for this session"
        )
    
    # Check signup limit
    current_count, max_limit = crud.check_session_signup_limit(session, session_id)
    if max_limit and current_count >= max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This demo session is full"
        )
    
    # Validate demo ownership if provided
    if signup_data.demo_id:
        demo = crud.get_demo(session, signup_data.demo_id)
        if not demo or demo.student_id != db_student.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Demo not found or does not belong to you"
            )
    
    # Create signup
    signup = crud.create_demo_signup(
        session, session_id, db_student.id, signup_data
    )
    session.commit()
    session.refresh(signup)
    
    return signup


@router.get(
    "/students/me/demo-signups",
    response_model=List[DemoSignupRead],
    summary="My Demo Signups",
    tags=["My Student Data"],
)
def list_my_demo_signups(
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    """List all demo signups for the current student"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their signups"
        )
    
    db_student = session.query(Student).filter(Student.user_id == current_user.id).first()
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    signups = crud.get_demo_signups_by_student(session, db_student.id)
    return signups


@router.put(
    "/demo-signups/{signup_id}",
    response_model=DemoSignupRead,
    summary="Update My Demo Signup",
    tags=["Demo Sessions"],
)
def update_my_demo_signup(
    signup_id: int,
    signup_update: DemoSignupUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    """Update a demo signup (student can only update their own)"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can update their signups"
        )
    
    # Get student info
    db_student = session.query(Student).filter(Student.user_id == current_user.id).first()
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Get signup
    db_signup = crud.get_demo_signup(session, signup_id)
    if not db_signup or db_signup.student_id != db_student.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo signup not found or does not belong to you"
        )
    
    # Validate demo ownership if being updated
    if signup_update.demo_id:
        demo = crud.get_demo(session, signup_update.demo_id)
        if not demo or demo.student_id != db_student.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Demo not found or does not belong to you"
            )
    
    # Update signup
    updated_signup = crud.update_demo_signup(session, db_signup, signup_update)
    session.commit()
    session.refresh(updated_signup)
    
    return updated_signup


@router.delete(
    "/demo-signups/{signup_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel My Demo Signup",
    tags=["Demo Sessions"],
)
def cancel_my_demo_signup(
    signup_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    """Cancel a demo signup"""
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can cancel their signups"
        )
    
    # Get student info
    db_student = session.query(Student).filter(Student.user_id == current_user.id).first()
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Get signup
    db_signup = crud.get_demo_signup(session, signup_id)
    if not db_signup or db_signup.student_id != db_student.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo signup not found or does not belong to you"
        )
    
    # Delete signup
    crud.delete_demo_signup(session, db_signup)
    session.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
