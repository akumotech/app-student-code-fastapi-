from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class OverviewStats(BaseModel):
    total_students: int
    total_certificates: int
    total_demos: int
    students_with_certificates: int
    students_with_demos: int
    avg_certificates_per_student: float
    avg_demos_per_student: float

class TrendsStats(BaseModel):
    labels: List[str]
    new_students: List[int]
    certificates_issued: List[int]
    demos_submitted: List[int]

class EngagementStats(BaseModel):
    inactive_students_7d: int
    inactive_students_30d: int
    active_streaks: List[Dict[str, Any]]
    at_risk_students: List[int]

class CodingActivityStats(BaseModel):
    total_coding_seconds: float
    per_student: Dict[str, float]
    per_language: Dict[str, float]
    heatmap: Dict[int, Dict[int, float]]
    inactive_students: List[int] 