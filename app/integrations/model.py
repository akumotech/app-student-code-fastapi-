from pydantic import BaseModel, EmailStr


class WakaTimeCallbackPayload(BaseModel):
    code: str 
    state: str | None = None 

class WakaTimeUsageRequest(BaseModel):
    email: EmailStr