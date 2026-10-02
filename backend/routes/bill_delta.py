from fastapi import APIRouter
from agents.bill_agent import BillAgent
from schemas.models import BillDeltaRequest

router = APIRouter()
agent = BillAgent()


@router.post("")
async def get_bill_delta(body: BillDeltaRequest):
    return await agent.run(body.customer_id, body.current_plan, body.proposed_change)
