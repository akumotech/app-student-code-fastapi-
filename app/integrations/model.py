from pydantic import BaseModel


class WakaTimeCallbackPayload(BaseModel):
    code: str 
    state: str | None = None 

class WakaTimeUsageRequest(BaseModel):
    email: str