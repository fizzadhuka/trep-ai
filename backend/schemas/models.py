from pydantic import BaseModel
from typing import Optional, List


class BriefResponse(BaseModel):
    plan_summary: str
    upgrade_status: str
    bill_summary: str
    open_issues: List[str]
    pah_status: str


class BillDeltaResponse(BaseModel):
    delta_dollars: float
    direction: str  # "increase" | "decrease" | "none"
    explanation: str
    new_monthly_total: float


class IntentResponse(BaseModel):
    topic: str
    details: dict
    action: str
    confidence: float
    data_to_surface: Optional[dict] = None


class PAHCheckResponse(BaseModel):
    is_authorized: bool
    permitted_actions: List[str]
    restricted_actions: List[str]
    authorization_options: List[str]
    explanation: str


class IntentRequest(BaseModel):
    transcript: str
    customer_id: str


class BillDeltaRequest(BaseModel):
    customer_id: str
    current_plan: str
    proposed_change: str
