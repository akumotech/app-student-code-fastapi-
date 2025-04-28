from pydantic import BaseModel
from typing import Optional

class StudentCreate(BaseModel):
    user_id: int
    batch: str
    project: str

class StudentRead(BaseModel):
    id: int
    user_id: int
    batch: str
    project: str 