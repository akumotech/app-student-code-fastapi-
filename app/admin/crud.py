from sqlmodel import Session, select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from app.auth.models import User
from app.students.models import Student, Batch, Project, Certificate, Demo
from app.integrations.model import DailySummary
from .schemas import StudentUpdate


def get_all_users_with_details(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    role_filter: Optional[str] = None
) -> Tuple[List[User], int]:
    """Get all users with their related data for admin overview"""
    
    # Build base query with eager loading
    query = (
        select(User)
        .options(
            selectinload(User.student_batches),
            selectinload(User.instructor_batches)
        )
        .order_by(User.id)
    )
    
    # Apply role filter if specified
    if role_filter and role_filter != "all":
        query = query.where(User.role == role_filter)
    
    # Get total count
    count_query = select(func.count(User.id))
    if role_filter and role_filter != "all":
        count_query = count_query.where(User.role == role_filter)
    
    total_count = db.exec(count_query).one()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    users = db.exec(query).all()
    
    return users, total_count


def get_student_by_user_id(db: Session, user_id: int) -> Optional[Student]:
    """Get student record with all related data"""
    query = (
        select(Student)
        .options(
            selectinload(Student.batch),
            selectinload(Student.project),
            selectinload(Student.certificates),
            selectinload(Student.demos)
        )
        .where(Student.user_id == user_id)
    )
    return db.exec(query).first()


def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    """Get student by student ID with all related data"""
    query = (
        select(Student)
        .options(
            selectinload(Student.batch),
            selectinload(Student.project),
            selectinload(Student.certificates),
            selectinload(Student.demos)
        )
        .where(Student.id == student_id)
    )
    return db.exec(query).first()


def update_student(db: Session, student_id: int, student_update: StudentUpdate) -> Optional[Student]:
    """Update student information"""
    student = db.get(Student, student_id)
    if not student:
        return None
    
    update_data = student_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)
    
    db.add(student)
    db.commit()
    db.refresh(student)
    
    # Reload with relationships
    return get_student_by_id(db, student_id)


def get_recent_wakatime_stats(db: Session, user_id: int, days: int = 7) -> Optional[dict]:
    """Get recent WakaTime statistics for a user, including average per day."""
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    query = (
        select(DailySummary)
        .where(
            DailySummary.user_id == user_id,
            DailySummary.date >= start_date,
            DailySummary.date <= end_date
        )
        .order_by(DailySummary.date.desc())
    )
    
    summaries = db.exec(query).all()
    
    if not summaries:
        return None
    
    # Calculate totals
    total_seconds = sum(summary.total_seconds for summary in summaries)
    total_days = len(summaries)
    avg_seconds = total_seconds / total_days if total_days else 0
    avg_hours = int(avg_seconds // 3600)
    avg_minutes = int((avg_seconds % 3600) // 60)
    avg_digital = f"{avg_hours:02d}:{avg_minutes:02d}"
    if avg_hours > 0:
        avg_text = f"{avg_hours} hrs {avg_minutes} mins"
    else:
        avg_text = f"{avg_minutes} mins"
    
    # Format digital time for total
    total_hours = int(total_seconds // 3600)
    total_minutes = int((total_seconds % 3600) // 60)
    digital = f"{total_hours:02d}:{total_minutes:02d}"
    if total_hours > 0:
        text = f"{total_hours} hrs {total_minutes} mins"
    else:
        text = f"{total_minutes} mins"
    
    return {
        "total_seconds": total_seconds,
        "hours": total_hours,
        "minutes": total_minutes,
        "digital": digital,
        "text": text,
        "last_updated": summaries[0].cached_at if summaries else None,
        "average_seconds": avg_seconds,
        "average_hours": avg_hours,
        "average_minutes": avg_minutes,
        "average_digital": avg_digital,
        "average_text": avg_text,
        "days_counted": total_days
    }


def get_dashboard_statistics(db: Session) -> dict:
    """Get comprehensive dashboard statistics"""
    
    # User counts by role
    user_stats = db.exec(
        select(User.role, func.count(User.id))
        .group_by(User.role)
    ).all()
    
    role_counts = {role: count for role, count in user_stats}
    
    # Total counts
    total_users = db.exec(select(func.count(User.id))).one()
    total_students = role_counts.get("student", 0)
    total_instructors = role_counts.get("instructor", 0)
    total_admins = role_counts.get("admin", 0)
    
    # Active batches (assuming active means currently running)
    today = datetime.utcnow().date()
    active_batches = db.exec(
        select(func.count(Batch.id))
        .where(
            Batch.start_date <= today,
            Batch.end_date >= today
        )
    ).one()
    
    # Certificate and demo counts
    total_certificates = db.exec(select(func.count(Certificate.id))).one()
    total_demos = db.exec(select(func.count(Demo.id))).one()
    
    # Users with WakaTime connected
    users_with_wakatime = db.exec(
        select(func.count(User.id))
        .where(User.wakatime_access_token_encrypted.is_not(None))
    ).one()
    
    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_instructors": total_instructors,
        "total_admins": total_admins,
        "active_batches": active_batches,
        "total_certificates": total_certificates,
        "total_demos": total_demos,
        "users_with_wakatime": users_with_wakatime
    }


def get_recent_students(db: Session, limit: int = 10) -> List[User]:
    """Get recently created student users"""
    query = (
        select(User)
        .where(User.role == "student")
        .order_by(User.id.desc())
        .limit(limit)
    )
    return db.exec(query).all()


def get_active_batches(db: Session) -> List[Batch]:
    """Get currently active batches"""
    today = datetime.utcnow().date()
    query = (
        select(Batch)
        .where(
            Batch.start_date <= today,
            Batch.end_date >= today
        )
        .order_by(Batch.start_date)
    )
    return db.exec(query).all()


def get_all_batches(db: Session) -> List[Batch]:
    """Get all batches for admin management"""
    query = select(Batch).order_by(Batch.name)
    return db.exec(query).all()


def get_all_projects(db: Session) -> List[Project]:
    """Get all projects for admin management"""
    query = select(Project).order_by(Project.name)
    return db.exec(query).all()


def search_users(db: Session, search_term: str, limit: int = 50) -> List[User]:
    """Search users by name or email"""
    search_pattern = f"%{search_term}%"
    query = (
        select(User)
        .where(
            (User.name.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )
        .limit(limit)
    )
    return db.exec(query).all()
