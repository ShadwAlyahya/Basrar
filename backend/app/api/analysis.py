from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.agent.analyst import LeadAnalystAgent

router = APIRouter(prefix="/analysis", tags=["AI Analysis"])

class AnalysisRequest(BaseModel):
    dataset_id: int
    query: str

@router.post("/query")
def query_dataset(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.user_id == current_user.id
    ).first()

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found or unauthorized access."
        )

    agent = LeadAnalystAgent(dataset.file_path)
    return agent.process_query(request.query)