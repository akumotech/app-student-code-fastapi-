from sqlmodel import SQLModel, Field

class Student(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    batch: str
    project: str
    # Add more student-specific fields as needed