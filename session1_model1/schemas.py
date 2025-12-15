from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from models import Status, Priority

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Status = Status.PENDING
    priority: Priority

    model_config = {"from_attributes": True}

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None

class TaskResponse(TaskBase):
    id: int
    created_at: datetime