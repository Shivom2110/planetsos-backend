"""Schemas for risk assessment feedback and training summaries."""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high", "critical"]


class RiskFeedbackRequest(BaseModel):
    """Verified outcome used to improve future risk predictions."""

    final_category: str = Field(..., min_length=1, max_length=100)
    final_risk_level: RiskLevel
    final_responder_type: str = Field(..., min_length=1, max_length=100)
    final_status: str = Field(default="resolved", min_length=1, max_length=50)
    emergency_escalated: bool = False
    responder_notes: Optional[str] = Field(default=None, max_length=2000)
    was_prediction_correct: Optional[bool] = None


class RiskFeedbackResponse(BaseModel):
    """Confirmation that a verified outcome was recorded for training."""

    ticket_id: str
    training_recorded: bool
    model_version: str
    feedback_summary: Dict[str, Any]


class RiskTrainingSummary(BaseModel):
    """Aggregate metrics describing the local training signal."""

    model_version: str
    total_feedback_records: int
    issue_type_stats: Dict[str, Dict[str, int]]
    risk_distribution: Dict[str, int]
    responder_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    average_prediction_accuracy: float
