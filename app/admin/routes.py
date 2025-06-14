from fastapi import APIRouter, Depends, HTTPException, status, Query
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
from app.core.schemas import APIResponse

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
