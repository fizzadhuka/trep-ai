import asyncio
import time
from services.bill_service import (
    calculate_new_bill as svc_calculate_new_bill,
    resolve_plan_id,
    BillError,
    CUSTOMERS,
)

STEP_DEFINITIONS = {
    "trade_in_upgrade": [
        {"id": 1, "name": "Verifying account identity",       "duration_ms": 1000},
        {"id": 2, "name": "Confirming trade-in value",        "duration_ms": 1200},
        {"id": 3, "name": "Applying upgrade promotion",        "duration_ms": 800,  "error_step": True},
        {"id": 4, "name": "Processing plan change",           "duration_ms": 1500},
        {"id": 5, "name": "Entering order into DASH",         "duration_ms": 1000},
        {"id": 6, "name": "Generating updated bill",          "duration_ms": 800},
    ],
    "plan_upgrade_only": [
        {"id": 1, "name": "Verifying account identity",       "duration_ms": 1000},
        {"id": 2, "name": "Checking plan eligibility",        "duration_ms": 800},
        {"id": 3, "name": "Processing plan change",           "duration_ms": 1500},
        {"id": 4, "name": "Entering order into DASH",         "duration_ms": 1000},
        {"id": 5, "name": "Generating updated bill",          "duration_ms": 800},
    ],
}


class ExecutionService:
    def get_step_definitions(self, transaction_type: str) -> list:
        return STEP_DEFINITIONS.get(transaction_type, STEP_DEFINITIONS["trade_in_upgrade"])

    def calculate_new_bill(self, customer_id: str, params: dict) -> dict:
        transaction = {"account_id": customer_id}

        # Accept display name ("Magenta MAX") or plan_id ("magenta_max")
        proposed = params.get("proposed_plan") or params.get("to_plan_id", "")
        if proposed:
            try:
                transaction["to_plan_id"] = resolve_plan_id(proposed)
            except BillError:
                pass

        if params.get("new_device"):
            transaction["new_device"] = params["new_device"]

        # Infer trade_in_device from customer data if only trade_in_value given
        trade_in_device = params.get("trade_in_device")
        if not trade_in_device and params.get("trade_in_value"):
            customer = CUSTOMERS.get(customer_id, {})
            trade_in_device = customer.get("upgrade_eligibility", {}).get("current_device")
        if trade_in_device:
            transaction["trade_in_device"] = trade_in_device

        if params.get("lines_delta"):
            transaction["lines_delta"] = params["lines_delta"]

        result = svc_calculate_new_bill(transaction)
        # Add string alias so FinalBillCard can read promo_applied directly
        promos = result.get("promos_applied", [])
        result["promo_applied"] = promos[0]["name"] if promos else None
        return result

    async def stream_steps(self, transaction_type: str, customer_id: str, params: dict, send_fn):
        steps = self.get_step_definitions(transaction_type)
        completed = []
        start_time = time.monotonic()

        for step in steps:
            await send_fn({"type": "step", "id": step["id"], "name": step["name"], "status": "active"})
            await asyncio.sleep(step["duration_ms"] / 1000)

            # Step 3 of trade_in_upgrade: simulate promo validation timeout + auto-retry
            if step.get("error_step") and transaction_type == "trade_in_upgrade":
                await send_fn({"type": "step", "id": step["id"], "name": step["name"], "status": "error", "message": "Promo validation timeout"})
                await asyncio.sleep(0.5)
                await send_fn({"type": "step", "id": step["id"], "name": step["name"], "status": "retrying"})
                await asyncio.sleep(1.5)

            await send_fn({"type": "step", "id": step["id"], "name": step["name"], "status": "complete"})
            completed.append(step["id"])

        final_bill = self.calculate_new_bill(customer_id, params)
        await send_fn({
            "type": "done",
            "steps_completed": len(completed),
            "duration_seconds": round(time.monotonic() - start_time, 1),
            "final_bill": final_bill,
            "promo_applied": final_bill.get("promo_applied"),
        })
