"""POST /pah-check — what a visiting person is allowed to do. Owner: P1b.

The point is not to turn a non-PAH visitor away. It is to tell the rep what
they *can* still do, so a dead end becomes a partial win.
"""

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from schemas.models import PAHCheckResponse
from services.llm_service import LLMService

router = APIRouter()
llm = LLMService()

_customers = json.loads((Path(__file__).parent.parent / "mock/customers.json").read_text())

PERMITTED_PAH = [
    "Add or remove lines",
    "Upgrade device",
    "Change plan",
    "Add authorized users",
    "View account information",
    "Pay bill",
]
PERMITTED_NON_PAH = [
    "View account information",
    "Pay bill",
    "Purchase accessories",
    "Get a written quote",
    "Start a port-in from another carrier",
]
RESTRICTED_NON_PAH = [
    "Add or remove lines",
    "Upgrade device",
    "Change plan",
    "Add authorized users",
]


class PAHCheckRequest(BaseModel):
    account_id: str
    visiting_user_name: str


class PAHCheckDetail(PAHCheckResponse):
    """Adds display context on top of the shared contract."""

    pah_name: str
    pah_present: bool
    visiting_user_name: str


def _names_match(a: str, b: str) -> bool:
    """Require a full-name match, not a substring.

    Substring matching authorises anyone named "Patel" on the Patel account,
    which is exactly the check this endpoint exists to perform.
    """
    at = {t for t in re.split(r"\W+", a.lower()) if t}
    bt = {t for t in re.split(r"\W+", b.lower()) if t}
    if not at or not bt:
        return False
    return at == bt or (len(at) >= 2 and at.issubset(bt))


def _fallback_explanation(name: str, pah_name: str, authorized: bool) -> str:
    if authorized:
        return f"{name} is an authorized user on this account and can make changes."
    return (
        f"{name} isn't an authorized user on this account — {pah_name} is the primary "
        f"account holder. You can still view the account, take a payment, or write up a "
        f"quote, but any plan or device change needs {pah_name} to authorize it."
    )


@router.post("", response_model=PAHCheckDetail)
async def pah_check(body: PAHCheckRequest):
    customer = next((c for c in _customers if c["account_id"] == body.account_id), None)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    pah = customer.get("primary_holder", {})
    pah_name = pah.get("name", "the primary account holder")
    authorized_users = customer.get("authorized_users", [])

    is_authorized = any(_names_match(body.visiting_user_name, n) for n in authorized_users)

    prompt = (
        "You are helping a T-Mobile retail rep. Write ONE short sentence the rep can say "
        "out loud to the customer in front of them.\n\n"
        f"Visitor: {body.visiting_user_name}\n"
        f"Primary account holder: {pah_name}\n"
        f"Authorized on this account: {'yes' if is_authorized else 'no'}\n\n"
        + (
            "Confirm warmly that they're all set to make changes today."
            if is_authorized
            else "Explain kindly that account changes need the primary holder's authorization, "
            "and point out what you CAN help with right now (viewing the account, taking a "
            "payment, writing up a quote). Do not sound like a rejection."
        )
        + "\n\nRules: one sentence, no preamble, no markdown, no quotes."
    )

    try:
        raw = await llm.complete(prompt)
        explanation = (raw or "").strip().strip('"').splitlines()[0].strip()
        if not explanation:
            raise ValueError("empty explanation")
    except Exception:
        explanation = _fallback_explanation(body.visiting_user_name, pah_name, is_authorized)

    return {
        "is_authorized": is_authorized,
        "permitted_actions": PERMITTED_PAH if is_authorized else PERMITTED_NON_PAH,
        "restricted_actions": [] if is_authorized else RESTRICTED_NON_PAH,
        "authorization_options": [] if is_authorized else [
            "Request Remote Authorization (PAH calls in)",
            "Have PAH come into store",
        ],
        "explanation": explanation,
        "pah_name": pah_name,
        "pah_present": bool(pah.get("is_present", False)),
        "visiting_user_name": body.visiting_user_name,
    }
