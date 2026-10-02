from fastapi import APIRouter, HTTPException
from agents.brief_agent import BriefAgent
from pathlib import Path
import json

router = APIRouter()
agent = BriefAgent()
_customers = json.loads((Path(__file__).parent.parent / "mock/customers.json").read_text())
_cache: dict = {}


@router.get("/{customer_id}")
async def get_brief(customer_id: str):
    customer = next((c for c in _customers if c["account_id"] == customer_id), None)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer_id not in _cache:
        _cache[customer_id] = await agent.run(customer)
    return _cache[customer_id]


@router.delete("/{customer_id}/cache")
def bust_brief_cache(customer_id: str):
    _cache.pop(customer_id, None)
    return {"cleared": customer_id}
