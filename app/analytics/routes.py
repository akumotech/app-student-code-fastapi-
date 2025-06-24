from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.analytics.services import get_overview_stats, get_trends, get_engagement_stats, get_coding_activity_stats
from app.analytics.schemas import OverviewStats, TrendsStats, EngagementStats, CodingActivityStats
from app.auth.utils import get_current_active_user
from app.auth.database import get_session
from app.auth.models import User as UserSchema

router = APIRouter(prefix="/api/v1/admin", tags=["Analytics"])

def require_admin(current_user: UserSchema):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")

@router.get("/overview", response_model=OverviewStats)
def overview(
    batch_id: int = Query(None, description="Batch ID for per-batch analytics"),
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_admin(current_user)
    return get_overview_stats(session, batch_id=batch_id)

@router.get("/trends", response_model=TrendsStats)
def trends(
    batch_id: int = Query(None, description="Batch ID for per-batch analytics"),
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_admin(current_user)
    return get_trends(session, batch_id=batch_id)

@router.get("/engagement", response_model=EngagementStats)
def engagement(
    batch_id: int = Query(None, description="Batch ID for per-batch analytics"),
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_admin(current_user)
    return get_engagement_stats(session, batch_id=batch_id)

@router.get("/coding-activity", response_model=CodingActivityStats)
def coding_activity(
    batch_id: int = Query(None, description="Batch ID for per-batch analytics"),
    session: Session = Depends(get_session),
    current_user: UserSchema = Depends(get_current_active_user),
):
    require_admin(current_user)
    return get_coding_activity_stats(session, batch_id=batch_id) 