from pydantic import BaseModel


class UserRoleUpdate(BaseModel):
    role: str
