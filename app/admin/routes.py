from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlmodel import Session
from typing import Any, Optional, List

from app.auth import crud as auth_crud
from app.auth.database import get_session
from app.auth.utils import get_current_active_user
from app.auth.schemas import User as UserSchema
from app.auth.models import User
from app.students.models import Student

from . import crud as admin_crud
from .schemas import (
    UserRoleUpdate, 
    StudentUpdate,
    UserOverview, 
    AdminUsersList,
    AdminDashboard,
    DashboardStats,
    StudentDetail,
    UserBasic,
    CertificateInfo,
    DemoInfo,
    BatchInfo,
    ProjectInfo,
    WakaTimeStats
)
from app.students.schemas import (
    DemoSessionCreate,
    DemoSessionUpdate,
    DemoSessionRead,
    DemoSignupRead,
    DemoSignupAdminUpdate,
)
from app.core.schemas import APIResponse
from app.analytics import services as analytics_service

router = APIRouter(
    tags=["Admin"],
)

VALID_ROLES = ["student", "instructor", "admin", "user"]


def require_admin_role(current_user: UserSchema = Depends(get_current_active_user)):
    """Dependency to ensure admin access"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action.",
        )
    return current_user


def get_current_admin_user(current_user: UserSchema = Depends(get_current_active_user)):
    """Alias for require_admin_role for consistency"""
    return require_admin_role(current_user)


def convert_user_to_overview(user: User, student: Optional[Student] = None, wakatime_stats: Optional[dict] = None) -> UserOverview:
    """Convert User model to UserOverview schema"""
    
    student_detail = None
    if student:
        # Convert related objects to schemas
        batch_info = BatchInfo.model_validate(student.batch) if student.batch else None
        project_info = ProjectInfo.model_validate(student.project) if student.project else None
        certificates = [CertificateInfo.model_validate(cert) for cert in student.certificates]
        demos = [DemoInfo.model_validate(demo) for demo in student.demos]
        
        wakatime_stats_schema = None
        if wakatime_stats:
            wakatime_stats_schema = WakaTimeStats(**wakatime_stats)
        
        student_detail = StudentDetail(
            id=student.id,
            user=UserBasic.model_validate(user),
            batch=batch_info,
            project=project_info,
            certificates=certificates,
            demos=demos,
            wakatime_stats=wakatime_stats_schema
        )
    
    return UserOverview(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        disabled=user.disabled,
        student_detail=student_detail,
        wakatime_connected=bool(user.wakatime_access_token_encrypted),
        last_login=None  # TODO: Add last_login tracking to User model
    )


@router.get(
    "/dashboard",
    response_model=APIResponse,
    summary="Admin Dashboard Overview",
    dependencies=[Depends(require_admin_role)]
)
async def get_admin_dashboard(db: Session = Depends(get_session)):
    """Get comprehensive dashboard data for admin overview"""
    
    try:
        # Get dashboard statistics
        stats = admin_crud.get_dashboard_statistics(db)
        dashboard_stats = DashboardStats(**stats)
        
        # Get recent students
        recent_student_users = admin_crud.get_recent_students(db, limit=5)
        recent_students = []
        for user in recent_student_users:
            student = admin_crud.get_student_by_user_id(db, user.id)
            wakatime_stats = admin_crud.get_recent_wakatime_stats(db, user.id) if user.wakatime_access_token_encrypted else None
            recent_students.append(convert_user_to_overview(user, student, wakatime_stats))
        
        # Get active batches
        active_batches_data = admin_crud.get_active_batches(db)
        active_batches = [BatchInfo.model_validate(batch) for batch in active_batches_data]
        
        dashboard_data = AdminDashboard(
            stats=dashboard_stats,
            recent_students=recent_students,
            active_batches=active_batches
        )
        
        return APIResponse(
            success=True,
            message="Dashboard data retrieved successfully",
            data=dashboard_data.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving dashboard data: {str(e)}"
        )


@router.get(
    "/users",
    response_model=APIResponse,
    summary="Get All Users with Pagination and Filtering",
    dependencies=[Depends(require_admin_role)]
)
async def get_all_users(
    db: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role (student, instructor, admin, user)"),
    search: Optional[str] = Query(None, description="Search by name or email")
):
    """Get paginated list of all users with their details"""
    
    try:
        if search:
            # Use search functionality
            users = admin_crud.search_users(db, search, limit=page_size)
            total_count = len(users)
        else:
            # Use pagination with role filter
            skip = (page - 1) * page_size
            users, total_count = admin_crud.get_all_users_with_details(
                db, skip=skip, limit=page_size, role_filter=role
            )
        
        # Convert to overview format
        user_overviews = []
        for user in users:
            student = None
            wakatime_stats = None
            
            if user.role == "student":
                student = admin_crud.get_student_by_user_id(db, user.id)
            
            if user.wakatime_access_token_encrypted:
                wakatime_stats = admin_crud.get_recent_wakatime_stats(db, user.id)
            
            user_overviews.append(convert_user_to_overview(user, student, wakatime_stats))
        
        users_list = AdminUsersList(
            users=user_overviews,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(user_overviews)} users",
            data=users_list.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )


@router.get(
    "/users/{user_id}",
    response_model=APIResponse,
    summary="Get User Details",
    dependencies=[Depends(require_admin_role)]
)
async def get_user_details(
    user_id: int, 
    db: Session = Depends(get_session)
):
    """Get detailed information about a specific user"""
    
    user = auth_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    try:
        student = None
        wakatime_stats = None
        
        if user.role == "student":
            student = admin_crud.get_student_by_user_id(db, user_id)
        
        if user.wakatime_access_token_encrypted:
            wakatime_stats = admin_crud.get_recent_wakatime_stats(db, user_id)
        
        user_overview = convert_user_to_overview(user, student, wakatime_stats)
        
        return APIResponse(
            success=True,
            message="User details retrieved successfully",
            data=user_overview.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user details: {str(e)}"
        )


@router.put(
    "/users/{user_id}/role",
    response_model=APIResponse,
    summary="Admin: Update User Role",
    dependencies=[Depends(require_admin_role)],
)
async def admin_update_user_role(
    user_id: int, 
    role_update: UserRoleUpdate, 
    db: Session = Depends(get_session)
):
    """Update a user's role (admin only)"""
    
    if role_update.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}",
        )

    target_user: User | None = auth_crud.get_user_by_id(db, user_id=user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found.",
        )

    target_user.role = role_update.role
    db.add(target_user)
    try:
        db.commit()
        db.refresh(target_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role.",
        )

    return APIResponse(
        success=True,
        message=f"User {user_id}'s role updated to {role_update.role}.",
        data=UserBasic.model_validate(target_user).model_dump(),
    )


@router.put(
    "/students/{student_id}",
    response_model=APIResponse,
    summary="Update Student Information",
    dependencies=[Depends(require_admin_role)]
)
async def update_student_info(
    student_id: int,
    student_update: StudentUpdate,
    db: Session = Depends(get_session)
):
    """Update student batch or project assignment"""
    
    try:
        updated_student = admin_crud.update_student(db, student_id, student_update)
        if not updated_student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with id {student_id} not found"
            )
        
        # Get user info for complete response
        user = auth_crud.get_user_by_id(db, updated_student.user_id)
        wakatime_stats = None
        if user and user.wakatime_access_token_encrypted:
            wakatime_stats = admin_crud.get_recent_wakatime_stats(db, user.id)
        
        user_overview = convert_user_to_overview(user, updated_student, wakatime_stats)
        
        return APIResponse(
            success=True,
            message="Student information updated successfully",
            data=user_overview.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating student: {str(e)}"
        )


@router.get(
    "/batches",
    response_model=APIResponse,
    summary="Get All Batches",
    dependencies=[Depends(require_admin_role)]
)
async def get_all_batches(db: Session = Depends(get_session)):
    """Get all batches for admin management"""
    
    try:
        batches = admin_crud.get_all_batches(db)
        print("batches:", batches)
        batch_infos = [BatchInfo.model_validate(batch) for batch in batches]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(batch_infos)} batches",
            data=batch_infos
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving batches: {str(e)}"
        )


@router.get(
    "/projects",
    response_model=APIResponse,
    summary="Get All Projects",
    dependencies=[Depends(require_admin_role)]
)
async def get_all_projects(db: Session = Depends(get_session)):
    """Get all projects for admin management"""
    
    try:
        projects = admin_crud.get_all_projects(db)
        project_infos = [ProjectInfo.model_validate(project) for project in projects]
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(project_infos)} projects",
            data=project_infos
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving projects: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=APIResponse,
    summary="Get Dashboard Statistics",
    dependencies=[Depends(require_admin_role)]
)
async def get_dashboard_stats(db: Session = Depends(get_session)):
    """Get statistical overview for admin dashboard"""
    
    try:
        stats = admin_crud.get_dashboard_statistics(db)
        dashboard_stats = DashboardStats(**stats)
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=dashboard_stats.model_dump()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@router.get(
    "/students/{student_id}/full",
    response_model=APIResponse,
    summary="Get all data for a student (admin only)",
    dependencies=[Depends(require_admin_role)]
)
def get_full_student_data(
    student_id: int,
    db: Session = Depends(get_session)
):
    from app.admin.crud import get_student_by_id
    from app.auth.crud import get_user_by_id
    from app.admin.schemas import StudentDetail, UserBasic

    student = get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    user = get_user_by_id(db, student.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found for student")
    student_detail = StudentDetail(
        id=student.id,
        user=UserBasic.model_validate(user),
        batch=student.batch,
        project=student.project,
        certificates=student.certificates,
        demos=student.demos,
    )
    return APIResponse(
        success=True,
        message="Student detail retrieved",
        data=student_detail.model_dump()
    )

# --- Analytics endpoints ---
@router.get("/analytics/overview", response_model=dict, tags=["Analytics"])
def get_overview_analytics(
    batch_id: Optional[int] = None,
    db: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Get overview analytics"""
    try:
        return analytics_service.get_overview_stats(db, batch_id)
    except Exception as e:
        # Fallback to basic stats if analytics service doesn't exist
        return {"message": "Analytics service not available", "error": str(e)}


@router.get("/analytics/demos", response_model=List[dict], tags=["Analytics"])
def get_demo_trends(
    batch_id: Optional[int] = None,
    db: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Get demo trends over time"""
    try:
        return analytics_service.get_demo_trends(db, batch_id)
    except Exception as e:
        return [{"message": "Analytics service not available", "error": str(e)}]


@router.get("/analytics/wakatime", response_model=List[dict], tags=["Analytics"])
def get_wakatime_trends(
    batch_id: Optional[int] = None,
    db: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Get WakaTime activity trends"""
    try:
        return analytics_service.get_wakatime_trends(db, batch_id)
    except Exception as e:
        return [{"message": "Analytics service not available", "error": str(e)}]


# --- Demo Session Management (Admin) ---
@router.get(
    "/demo-sessions",
    response_model=List[DemoSessionRead],
    summary="List Demo Sessions",
    tags=["Demo Sessions"],
)
def list_demo_sessions(
    include_inactive: bool = False,
    include_cancelled: bool = False,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """List all demo sessions with optional filtering"""
    from app.students.crud import get_demo_sessions_with_signup_counts
    
    sessions_data = get_demo_sessions_with_signup_counts(session)
    
    result = []
    for demo_session, signup_count, _ in sessions_data:
        # Filter based on admin preferences
        if not include_inactive and not demo_session.is_active:
            continue
        if not include_cancelled and demo_session.is_cancelled:
            continue
            
        session_dict = demo_session.dict()
        session_dict["signup_count"] = signup_count
        session_dict["signups"] = []  # Will be populated if needed
        result.append(session_dict)
    
    return result


@router.post(
    "/demo-sessions",
    response_model=DemoSessionRead,
    summary="Create Demo Session",
    tags=["Demo Sessions"],
)
async def create_demo_session(
    demo_session_create: DemoSessionCreate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Create a new demo session with manual meeting link entry and optional Slack notification"""
    from app.students.crud import create_demo_session, get_demo_session_by_date
    from app.integrations.slack import send_demo_session_notification
    
    # Check if session already exists for this date
    existing_session = get_demo_session_by_date(
        session, demo_session_create.session_date
    )
    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demo session already exists for this date"
        )
    
    # Create the demo session
    demo_session = create_demo_session(session, demo_session_create)
    session.commit()
    session.refresh(demo_session)
    
    # Send Slack notification only if meeting link is provided
    if demo_session.zoom_link:
        try:
            # Format session time for display
            session_time_str = demo_session.session_time.strftime("%I:%M %p")
            
            await send_demo_session_notification(
                session_date=demo_session.session_date,
                session_title=demo_session.title,
                meeting_link=demo_session.zoom_link,
                description=demo_session.description,
                session_time=session_time_str
            )
            print("Slack notification sent successfully")
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            # Continue even if Slack notification fails
    
    # Convert to response format
    session_dict = demo_session.dict()
    session_dict["signup_count"] = 0
    session_dict["signups"] = []
    
    return session_dict


@router.get(
    "/demo-sessions/{session_id}",
    response_model=DemoSessionRead,
    summary="Get Demo Session",
    tags=["Demo Sessions"],
)
def get_demo_session_detail(
    session_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Get detailed info about a demo session including signups"""
    from app.students.crud import get_demo_session, get_demo_signups_by_session
    
    demo_session = get_demo_session(session, session_id)
    if not demo_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found"
        )
    
    # Get signups for this session
    signups = get_demo_signups_by_session(session, session_id)
    
    session_dict = demo_session.dict()
    session_dict["signup_count"] = len(signups)
    session_dict["signups"] = [signup.dict() for signup in signups]
    
    return session_dict


@router.put(
    "/demo-sessions/{session_id}",
    response_model=DemoSessionRead,
    summary="Update Demo Session",
    tags=["Demo Sessions"],
)
def update_demo_session(
    session_id: int,
    session_update: DemoSessionUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Update a demo session"""
    from app.students.crud import get_demo_session, update_demo_session
    
    db_session = get_demo_session(session, session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found"
        )
    
    updated_session = update_demo_session(session, db_session, session_update)
    session.commit()
    session.refresh(updated_session)
    
    # Convert to response format
    session_dict = updated_session.dict()
    session_dict["signup_count"] = 0  # Could be calculated if needed
    session_dict["signups"] = []
    
    return session_dict


@router.delete(
    "/demo-sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Demo Session",
    tags=["Demo Sessions"],
)
def delete_demo_session(
    session_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Delete a demo session and all associated signups"""
    from app.students.crud import get_demo_session, delete_demo_session
    
    db_session = get_demo_session(session, session_id)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found"
        )
    
    delete_demo_session(session, db_session)
    session.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Demo Signup Management (Admin) ---
@router.get(
    "/demo-sessions/{session_id}/signups",
    response_model=List[DemoSignupRead],
    summary="List Session Signups",
    tags=["Demo Sessions"],
)
def list_session_signups(
    session_id: int,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """List all signups for a specific demo session"""
    from app.students.crud import get_demo_session, get_demo_signups_by_session
    
    # Verify session exists
    demo_session = get_demo_session(session, session_id)
    if not demo_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found"
        )
    
    signups = get_demo_signups_by_session(session, session_id)
    return signups


@router.put(
    "/demo-signups/{signup_id}/admin",
    response_model=DemoSignupRead,
    summary="Update Signup (Admin)",
    tags=["Demo Sessions"],
)
def update_signup_admin(
    signup_id: int,
    admin_update: DemoSignupAdminUpdate,
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Update signup after presentation (admin only)"""
    from app.students.crud import get_demo_signup, update_demo_signup_admin
    
    db_signup = get_demo_signup(session, signup_id)
    if not db_signup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo signup not found"
        )
    
    updated_signup = update_demo_signup_admin(session, db_signup, admin_update)
    session.commit()
    session.refresh(updated_signup)
    
    return updated_signup


# --- Bulk Operations ---
@router.post(
    "/demo-sessions/bulk-create",
    response_model=List[DemoSessionRead],
    summary="Bulk Create Demo Sessions",
    tags=["Demo Sessions"],
)
def bulk_create_demo_sessions(
    sessions_data: List[DemoSessionCreate],
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_admin_user),
):
    """Create multiple demo sessions at once"""
    from app.students.crud import create_demo_session, get_demo_session_by_date
    
    created_sessions = []
    errors = []
    
    for session_create in sessions_data:
        try:
            # Check if session already exists
            existing = get_demo_session_by_date(
                session, session_create.session_date
            )
            if existing:
                errors.append(f"Session already exists for {session_create.session_date}")
                continue
            
            demo_session = create_demo_session(session, session_create)
            session_dict = demo_session.dict()
            session_dict["signup_count"] = 0
            session_dict["signups"] = []
            created_sessions.append(session_dict)
            
        except Exception as e:
            errors.append(f"Error creating session for {session_create.session_date}: {str(e)}")
    
    if errors:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Errors occurred: {'; '.join(errors)}"
        )
    
    session.commit()
    return created_sessions
