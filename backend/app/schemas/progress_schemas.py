from pydantic import BaseModel


class ProgressMetrics(BaseModel):
    speed_progress: float
    accuracy_progress: float
    time_progress: float
    consistency_score: float
