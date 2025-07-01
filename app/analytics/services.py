from sqlalchemy.orm import Session
from sqlalchemy.sql import func, text, extract
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Import models
from app.students.models import Student, Certificate, Demo, Batch
from app.integrations.model import DailySummary, Language
# from app.auth.models import User  # Uncomment if exists

# --- Overview Stats ---
def get_overview_stats(session: Session, batch_id: Optional[int] = None) -> Dict[str, Any]:
    query = session.query(Student)
    if batch_id:
        query = query.filter(Student.batch_id == batch_id)
    total_students = query.count()

    total_certificates = session.query(Certificate)
    if batch_id:
        total_certificates = total_certificates.join(Student).filter(Student.batch_id == batch_id)
    total_certificates = total_certificates.count()

    total_demos = session.query(Demo)
    if batch_id:
        total_demos = total_demos.join(Student).filter(Student.batch_id == batch_id)
    total_demos = total_demos.count()

    students_with_certificates = session.query(Student.id).join(Certificate).distinct()
    if batch_id:
        students_with_certificates = students_with_certificates.filter(Student.batch_id == batch_id)
    students_with_certificates = students_with_certificates.count()

    students_with_demos = session.query(Student.id).join(Demo).distinct()
    if batch_id:
        students_with_demos = students_with_demos.filter(Student.batch_id == batch_id)
    students_with_demos = students_with_demos.count()

    avg_certificates_per_student = (total_certificates / total_students) if total_students else 0
    avg_demos_per_student = (total_demos / total_students) if total_students else 0

    return {
        "total_students": total_students,
        "total_certificates": total_certificates,
        "total_demos": total_demos,
        "students_with_certificates": students_with_certificates,
        "students_with_demos": students_with_demos,
        "avg_certificates_per_student": avg_certificates_per_student,
        "avg_demos_per_student": avg_demos_per_student,
    }

# --- Trends ---
def get_trends(session: Session, batch_id: Optional[int] = None) -> Dict[str, Any]:
    # Monthly new students
    student_query = session.query(
        func.date_trunc('month', Batch.start_date if batch_id else Student.batch.start_date).label('month'),
        func.count(Student.id)
    )
    if batch_id:
        student_query = student_query.filter(Student.batch_id == batch_id)
    student_query = student_query.group_by('month').order_by('month')
    student_trends = student_query.all()

    # Monthly certificates
    cert_query = session.query(
        func.date_trunc('month', Certificate.date_issued).label('month'),
        func.count(Certificate.id)
    )
    if batch_id:
        cert_query = cert_query.join(Student).filter(Student.batch_id == batch_id)
    cert_query = cert_query.group_by('month').order_by('month')
    cert_trends = cert_query.all()

    # Monthly demos
    demo_query = session.query(
        func.date_trunc('month', Demo.demo_date).label('month'),
        func.count(Demo.id)
    )
    if batch_id:
        demo_query = demo_query.join(Student).filter(Student.batch_id == batch_id)
    demo_query = demo_query.group_by('month').order_by('month')
    demo_trends = demo_query.all()

    months = sorted(set([row[0] for row in student_trends + cert_trends + demo_trends if row[0]]))
    def trend_dict(trend):
        return {row[0].strftime('%Y-%m'): row[1] for row in trend if row[0]}
    student_dict = trend_dict(student_trends)
    cert_dict = trend_dict(cert_trends)
    demo_dict = trend_dict(demo_trends)
    return {
        "labels": months,
        "new_students": [student_dict.get(m.strftime('%Y-%m'), 0) for m in months],
        "certificates_issued": [cert_dict.get(m.strftime('%Y-%m'), 0) for m in months],
        "demos_submitted": [demo_dict.get(m.strftime('%Y-%m'), 0) for m in months],
    }

# --- Engagement ---
def get_engagement_stats(session: Session, batch_id: Optional[int] = None) -> Dict[str, Any]:
    # Last activity: use Demo, Certificate, or (optionally) CodingSession
    days_ago = lambda d: (datetime.utcnow().date() - d).days if d else None
    students = session.query(Student)
    if batch_id:
        students = students.filter(Student.batch_id == batch_id)
    students = students.all()
    inactive_7d = 0
    inactive_30d = 0
    active_streaks = []
    at_risk_students = []
    for s in students:
        last_demo = max([d.demo_date for d in s.demos if d.demo_date], default=None)
        last_cert = max([c.date_issued for c in s.certificates if c.date_issued], default=None)
        last_activity = max([d for d in [last_demo, last_cert] if d], default=None)
        if last_activity:
            days = days_ago(last_activity)
            if days >= 7:
                inactive_7d += 1
            if days >= 30:
                inactive_30d += 1
            if days <= 3:
                active_streaks.append({"student_id": s.id, "days": 3 - days})
            if days >= 14:
                at_risk_students.append(s.id)
        else:
            inactive_7d += 1
            inactive_30d += 1
            at_risk_students.append(s.id)
    return {
        "inactive_students_7d": inactive_7d,
        "inactive_students_30d": inactive_30d,
        "active_streaks": active_streaks,
        "at_risk_students": at_risk_students,
    }

# --- Coding Activity ---
def get_coding_activity_stats(session: Session, batch_id: Optional[int] = None) -> Dict[str, Any]:
    # Filter students by batch if needed
    student_query = session.query(Student.id)
    if batch_id:
        student_query = student_query.filter(Student.batch_id == batch_id)
    student_ids = [s[0] for s in student_query.all()]
    if not student_ids:
        return {
            "total_coding_seconds": 0,
            "per_student": {},
            "per_language": {},
            "heatmap": {},
            "inactive_students": [],
        }
    # Total coding time per student
    coding_per_student = dict(
        session.query(DailySummary.user_id, func.sum(DailySummary.total_seconds))
        .filter(DailySummary.user_id.in_(student_ids))
        .group_by(DailySummary.user_id)
        .all()
    )
    # Coding time per language
    lang_query = session.query(Language.name, func.sum(Language.total_seconds))
    lang_query = lang_query.join(DailySummary, Language.summary_id == DailySummary.id)
    lang_query = lang_query.filter(DailySummary.user_id.in_(student_ids))
    lang_query = lang_query.group_by(Language.name)
    per_language = dict(lang_query.all())
    # Activity heatmap (day of week x hour)
    heatmap = {}
    for dow, hour, total in session.query(
        extract('dow', DailySummary.start),
        extract('hour', DailySummary.start),
        func.sum(DailySummary.total_seconds)
    ).filter(DailySummary.user_id.in_(student_ids)).group_by(
        extract('dow', DailySummary.start), extract('hour', DailySummary.start)
    ):
        heatmap.setdefault(int(dow), {})[int(hour)] = float(total)
    # Inactive students (no coding in last 14 days)
    cutoff = datetime.utcnow().date() - timedelta(days=14)
    active_ids = set(
        r[0] for r in session.query(DailySummary.user_id)
        .filter(DailySummary.user_id.in_(student_ids), DailySummary.date >= cutoff)
        .distinct().all()
    )
    inactive_students = [sid for sid in student_ids if sid not in active_ids]
    return {
        "total_coding_seconds": float(sum(coding_per_student.values())),
        "per_student": {str(k): float(v) for k, v in coding_per_student.items()},
        "per_language": per_language,
        "heatmap": heatmap,
        "inactive_students": inactive_students,
    }

# TODO: Add curriculum analysis, coding activity, prediction, etc. 