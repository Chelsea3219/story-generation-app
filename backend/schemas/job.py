"""Schema folder will define the type of data that out API will be returning and the type of data that out API
will expect.

API is just a way for us to communicate data between different services.

We should define the types of data that we expect to come in and the types of data that we expect to come out"""

from typing import Optional
from datetime import datetime
from  pydantic import BaseModel

class StoryJobBase(BaseModel):
    theme: str

class StoryJobResponse(BaseModel):
    job_id:str
    status:str
    created_at:datetime
    story_id: Optional[int]=None
    completed_at: Optional[datetime]=None
    error: Optional[str]=None

    class Config:
        from_attributes=True

class StoryJobCreate(StoryJobBase): #Giving it a new name
    pass