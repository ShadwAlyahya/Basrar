from pydantic import BaseModel
from datetime import datetime

class DatasetResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    uploaded_at: datetime
    user_id: int

    class Config:
        from_attributes = True