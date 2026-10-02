import json
from pathlib import Path

from prompts.intent_prompt import build_intent_prompt
from services.llm_service import LLMService

_plans = json.loads((Path(__file__).parent.parent / "mock/plans.json").read_text())
_devices = json.loads((Path(__file__).parent.parent / "mock/devices.json").read_text())
_promos = json.loads((Path(__file__).parent.parent / "mock/promos.json").read_text())

# Actions the model sometimes invents that mean "show me the bill impact".
_DELTA_ACTIONS = {"calculate_delta", "fetch_billing_details", "fetch_bill"}

# The model is inconsistent about which action a question deserves: "how much
# more for Magenta MAX" returns calculate_delta, while "switch to Magenta MAX"
# returns fetch_plan — same question, but only one produced a number. These
# topics are cost questions by definition, so price them regardless of the
# action the model happened to pick.
_DELTA_TOPICS = {"plan_upgrade", "add_line", "billing", "device_inquiry", "trade_in"}

# The model names the same field differently run to run.
_PLAN_KEYS = ("plan_name", "requested_plan", "target_plan", "to_plan", "plan")
_DEVICE_KEYS = ("device_name", "device", "requested_device", "model")


def _first(details: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = details.get(key)
        if isinstance(value, str) and value.strip() and value.lower() != "unknown":
            return value.strip().lower()
    return ""


def _empty(customer_id: str) -> dict:
    return {"topic": "none", "details": {}, "action": "none", "confidence": 0.0,
            "customer_id": customer_id, "data_to_surface": {}}


class IntentAgent:
    def __init__(self):
        self.llm = LLMService()

    async def run(self, transcript: str, customer_id: str) -> dict:
        prompt = build_intent_prompt(transcript)

        # A gateway failure must not 500 the endpoint — the mic would look
        # broken because of an unrelated LLM problem.
        try:
            raw = await self.llm.complete(prompt)
        except Exception:
            return _empty(customer_id)

        try:
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(cleaned)
        except Exception:
            return _empty(customer_id)

        data_to_surface = {}
        action = result.get("action", "none")
        topic = result.get("topic", "none")
        details = result.get("details") or {}

        if action == "fetch_plan":
            # Narrow to the plan actually named; fall back to the catalog.
            # plans.json is keyed by plan_id, so iterate .values() — iterating
            # the dict itself yields the string keys and p["name"] raises.
            named = _first(details, _PLAN_KEYS)
            matched = [p for p in _plans.values() if named and named in p["name"].lower()]
            data_to_surface["plans"] = matched or list(_plans.values())

        elif action == "fetch_device":
            named = _first(details, _DEVICE_KEYS)
            matched = [d for d in _devices if named and named in d.get("model", "").lower()]
            data_to_surface["devices"] = matched or _devices

        elif action == "fetch_promo":
            data_to_surface["promos"] = _promos

        if action in _DELTA_ACTIONS or topic in _DELTA_TOPICS:
            # The moment the demo hinges on: the customer asks "how much more
            # would that be" and the number appears without the rep looking it
            # up. Detecting the intent and stopping there is a no-op.
            #
            # Computed here rather than shipping the catalog to the frontend to
            # divide — bill_service is the single source of pricing truth, and
            # a second implementation is how the brief card and the final bill
            # end up disagreeing on screen while a judge is watching.
            #
            # The raw transcript is passed straight through: BillAgent already
            # finds plans and devices inside a sentence and parses "add a line",
            # which is exactly the shape speech arrives in. Re-deriving them
            # from `details` here would be a worse copy of that, and `details`
            # keys change from run to run.
            try:
                from agents.bill_agent import BillAgent

                data_to_surface["bill_delta"] = await BillAgent().run(
                    customer_id, "", transcript
                )
            except Exception as exc:
                # Usually the customer named nothing priceable ("why is my bill
                # higher"). Report it rather than failing the whole intent call.
                data_to_surface["bill_delta_error"] = f"{type(exc).__name__}: {exc}"[:200]

        result["customer_id"] = customer_id
        result["data_to_surface"] = data_to_surface
        return result
