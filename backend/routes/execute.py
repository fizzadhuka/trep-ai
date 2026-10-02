from fastapi import APIRouter
from services.execution_service import ExecutionService
from schemas.execute import ExecuteRequest

router = APIRouter()
service = ExecutionService()


@router.get("/steps")
def get_steps(transaction_type: str = "trade_in_upgrade"):
    return service.get_step_definitions(transaction_type)


@router.post("/simulate")
async def simulate_execute(body: ExecuteRequest):
    """REST fallback — returns all steps as a completed list (no streaming)."""
    steps = service.get_step_definitions(body.transaction_type)
    return {
        "customer_id": body.customer_id,
        "transaction_type": body.transaction_type,
        "steps": [{"id": s["id"], "name": s["name"], "status": "complete"} for s in steps],
        "status": "done",
        "final_bill": service.calculate_new_bill(body.customer_id, body.params),
    }
