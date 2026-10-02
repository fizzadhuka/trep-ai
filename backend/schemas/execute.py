from pydantic import BaseModel


class ExecuteRequest(BaseModel):
    customer_id: str
    transaction_type: str  # "trade_in_upgrade" | "plan_upgrade_only"
    params: dict = {}
