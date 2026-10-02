from fastapi import APIRouter
from agents.intent_agent import IntentAgent
from schemas.models import IntentRequest

router = APIRouter()
agent = IntentAgent()


@router.post("")
async def detect_intent(body: IntentRequest):
    return await agent.run(body.transcript, body.customer_id)
