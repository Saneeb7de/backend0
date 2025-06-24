# schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

# Base model with shared attributes
class MeetingBase(BaseModel):
    title: str
    duration: int

# Schema for creating a new meeting (used for request body)
class MeetingCreate(MeetingBase):
    pass

# Schema for the response model (includes DB-generated fields)
class MeetingResponse(MeetingBase):
    id: int
    transcript: str
    created_at: datetime
    audio_path: str
    
    # Use model_config instead of the deprecated Config class
    model_config = ConfigDict(from_attributes=True)