"""Customer, device, and promotion lookups.  [P2]

ROUTE ORDER MATTERS. FastAPI matches in declaration order, so every static
path must be declared above /{customer_id} - otherwise a request to
/customer/promotions binds customer_id="promotions" and 404s. Add new
static routes above the marker comment, not below it.
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from services.bill_service import PLANS, BillError, resolve_plan_id, trade_in_offers

router = APIRouter()

_base = Path(__file__).parent.parent / "mock"
_customers = json.loads((_base / "customers.json").read_text())
_promos = json.loads((_base / "promos.json").read_text())

_BY_ACCOUNT = {c["account_id"]: c for c in _customers}


# --------------------------------------------------------------------------
# Static paths — must stay above /{customer_id}
# --------------------------------------------------------------------------

@router.get("/search")
def search_customer(q: str = Query(..., min_length=1)):
    """Fuzzy lookup by name, phone, or account id."""
    needle = q.strip().lower()
    return [
        c for c in _customers
        if needle in c.get("name", "").lower()
        or needle in c.get("phone", "")
        or needle in c.get("account_id", "")
    ][:10]


@router.get("/plans")
def list_plans():
    """Plan catalog. Powers BillExplorer's dropdown."""
    return list(PLANS.values())


@router.get("/promotions")
def get_promotions(
    from_plan: str = Query("", description="plan_id or display name"),
    to_plan: str = Query("", description="plan_id or display name"),
    has_trade_in: bool = Query(True),
    lines: int = Query(0, description="line count after the change; 0 = skip check"),
):
    """Promotions applicable to a plan change.

    Accepts plan_ids or display names on both sides. Returns [] rather than
    erroring on an unknown plan, since an empty promo list is a valid
    answer and P4 shouldn't have to handle a 4xx here.
    """
    try:
        from_id = resolve_plan_id(from_plan) if from_plan else ""
        to_id = resolve_plan_id(to_plan) if to_plan else ""
    except BillError:
        return []

    out = []
    for promo in _promos:
        if from_id and from_id not in promo.get("eligible_from_plans", []):
            continue
        if to_id and to_id not in promo.get("eligible_to_plans", []):
            continue
        if promo.get("requires_trade_in") and not has_trade_in:
            continue
        min_lines = promo.get("requires_min_lines")
        if min_lines is not None and lines and lines < min_lines:
            continue
        out.append(promo)
    return out


@router.get("/trade-in/{device_model}")
def get_trade_in(device_model: str):
    """What a device the customer owns is worth toward each new device.

    The path param is the phone being TRADED IN, not the one being bought.
    Value varies by target device - an iPhone 13 Pro is worth $320 against
    an iPhone 16 Pro but $280 against a base iPhone 16.
    """
    offers = trade_in_offers(device_model)
    best_model = max(offers, key=offers.get) if offers else None
    return {
        "device": device_model,
        "eligible": bool(offers),
        "offers": offers,
        "best_value": offers[best_model] if best_model else 0,
        "best_toward": best_model,
    }


# --------------------------------------------------------------------------
# Dynamic catch-all — keep last
# --------------------------------------------------------------------------

@router.get("/{customer_id}")
def get_customer(customer_id: str):
    customer = _BY_ACCOUNT.get(customer_id)
    if not customer:
        raise HTTPException(
            status_code=404,
            detail=f"Customer {customer_id} not found. "
                   f"Known accounts: {sorted(_BY_ACCOUNT)}",
        )
    return customer
