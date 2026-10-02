"""Bill calculation for T-Rep AI.  [P2]

Single source of truth for every dollar figure the product shows. P1's
/bill-delta and P3's execution engine must both call this - if either one
does its own arithmetic, the brief card and the final bill will disagree
on screen while a judge is watching.

    from services.bill_service import calculate_new_bill

    bill = calculate_new_bill({
        "account_id": "5550192",
        "to_plan_id": "magenta_max",
        "new_device": "iPhone 16 Pro",
        "trade_in_device": "iPhone 13 Pro",
    })
    bill["new_monthly_total"]   # 107.0

Transaction fields (only account_id is required):
    account_id         str   customer to bill
    to_plan_id         str   target plan; defaults to their current plan
    new_device         str   model from devices.json; omit for plan-only change
    trade_in_device    str   model being traded; omit for no trade-in
    lines_delta        int   +1 to add a line, -1 to remove; default 0
    financing_months   int   device term; default 24

All money is handled internally as integer cents. Floats are introduced
only at the boundary, when building the response. This matters: computing
$999/24 - $320/24 - $679/24 in floats and rounding each term to cents
yields $0.01 instead of $0.00, which would put a stray penny on the final
bill and make the "your trade-in fully covers the phone" claim false.
"""

from __future__ import annotations

import json
from pathlib import Path

_MOCK_DIR = Path(__file__).resolve().parent.parent / "mock"

DEFAULT_FINANCING_MONTHS = 24


def _load(filename: str):
    with open(_MOCK_DIR / filename) as fh:
        return json.load(fh)


# Loaded once at import. Mock data is static, so there's nothing to invalidate.
PLANS: dict = _load("plans.json")
PROMOS: list = _load("promos.json")
CUSTOMERS: dict = {c["account_id"]: c for c in _load("customers.json")}
DEVICES: dict = {d["model"]: d for d in _load("devices.json")}


class BillError(ValueError):
    """Raised for unknown accounts, plans, or devices."""


# Display name -> plan_id, so "Magenta MAX" and "magenta_max" both resolve.
_BY_DISPLAY_NAME = {p["name"].lower(): pid for pid, p in PLANS.items()}


def resolve_plan_id(value: str) -> str:
    """Accept a plan_id or a human display name and return the plan_id.

    The frontend sends whatever is in its dropdown, which is the display
    name ("Magenta MAX"). Accepting every reasonable spelling means P4
    doesn't have to care, and a stray hyphen can't silently produce a $0
    delta or an empty promo list.
    """
    if not value:
        raise BillError("plan is required")

    raw = str(value).strip()
    if raw in PLANS:
        return raw

    normalized = raw.lower().replace(" ", "_").replace("-", "_")
    if normalized in PLANS:
        return normalized
    if raw.lower() in _BY_DISPLAY_NAME:
        return _BY_DISPLAY_NAME[raw.lower()]

    raise BillError(
        f"unknown plan {value!r}; expected one of "
        f"{sorted(PLANS)} or {sorted(_BY_DISPLAY_NAME)}"
    )


def trade_in_offers(device_model: str) -> dict[str, float]:
    """What a customer-owned device is worth against each purchasable device.

    devices.json nests trade_in_values under the device being *bought*, so
    a device the customer already owns appears only as a key inside those
    maps - never as a top-level model. Matching against top-level models
    is what made this return empty for "iPhone 13 Pro".
    """
    if not device_model:
        return {}

    target = device_model.strip().lower()
    offers: dict[str, float] = {}
    for dev in DEVICES.values():
        for owned, value in dev["trade_in_values"].items():
            if owned.strip().lower() == target:
                offers[dev["model"]] = value
    return offers


def _cents(dollars) -> int:
    return int(round(float(dollars) * 100))


def _dollars(cents: int) -> float:
    return round(cents / 100, 2)


def plan_monthly_cents(plan_id: str, lines: int) -> int:
    """Monthly total for a plan at a given line count.

    Reads the explicit monthly_total_by_lines table rather than summing
    per-line rates, so there is exactly one interpretation of what a
    3-line account costs.
    """
    if plan_id not in PLANS:
        raise BillError(f"unknown plan_id {plan_id!r}; have {sorted(PLANS)}")

    table = PLANS[plan_id]["monthly_total_by_lines"]
    if lines < 1:
        raise BillError(f"lines must be >= 1, got {lines}")

    if str(lines) in table:
        return _cents(table[str(lines)])

    # Above the table's largest tier, extend using the marginal cost of the
    # last additional line. Keeps 6+ line accounts from silently clamping.
    tiers = sorted(int(k) for k in table)
    top = tiers[-1]
    marginal = _cents(table[str(top)]) - _cents(table[str(top - 1)])
    return _cents(table[str(top)]) + marginal * (lines - top)


def trade_in_cents(new_device: str | None, trade_in_device: str | None) -> int:
    """Trade-in value, which depends on the device being purchased.

    devices.json nests trade_in_values under each target device, so the same
    phone is worth more against an iPhone 16 Pro than an iPhone 16.
    """
    if not (new_device and trade_in_device):
        return 0
    if new_device not in DEVICES:
        raise BillError(f"unknown device {new_device!r}; have {sorted(DEVICES)}")
    return _cents(DEVICES[new_device]["trade_in_values"].get(trade_in_device, 0))


def eligible_promos(
    from_plan_id: str,
    to_plan_id: str,
    has_trade_in: bool,
    lines: int,
) -> list[dict]:
    """Promos this transaction qualifies for, driven entirely by promos.json."""
    out = []
    for promo in PROMOS:
        if from_plan_id not in promo["eligible_from_plans"]:
            continue
        if to_plan_id not in promo["eligible_to_plans"]:
            continue
        if promo.get("requires_trade_in") and not has_trade_in:
            continue
        min_lines = promo.get("requires_min_lines")
        if min_lines is not None and lines < min_lines:
            continue
        out.append(promo)
    return out


def calculate_new_bill(transaction: dict) -> dict:
    """Compute the post-transaction bill. Used by P3's execution engine."""
    account_id = str(transaction["account_id"])
    if account_id not in CUSTOMERS:
        raise BillError(f"unknown account_id {account_id!r}")

    customer = CUSTOMERS[account_id]
    current = customer["current_plan"]

    from_plan_id = current["plan_id"]
    to_plan_id = transaction.get("to_plan_id") or from_plan_id
    lines = current["lines"] + int(transaction.get("lines_delta", 0))
    months = int(transaction.get("financing_months", DEFAULT_FINANCING_MONTHS))

    new_device = transaction.get("new_device")
    trade_in_device = transaction.get("trade_in_device")

    if new_device and new_device not in DEVICES:
        raise BillError(f"unknown device {new_device!r}")

    # --- plan ---------------------------------------------------------------
    previous_c = plan_monthly_cents(from_plan_id, current["lines"])
    plan_c = plan_monthly_cents(to_plan_id, lines)

    # --- device, trade-in, and capped credits -------------------------------
    device_price_c = _cents(DEVICES[new_device]["price"]) if new_device else 0
    traded_c = trade_in_cents(new_device, trade_in_device)

    promos = eligible_promos(
        from_plan_id, to_plan_id, has_trade_in=traded_c > 0, lines=lines
    )

    # Balance owed on the device after trade-in. Credits apply against this
    # and never below zero - an uncapped $830 promo on a $999 phone with a
    # $320 trade-in would otherwise hand the customer $151 of negative bill.
    remaining_c = max(0, device_price_c - traded_c)

    applied, device_credit_c = [], 0
    for promo in promos:
        if promo["discount_type"] != "device_credit":
            continue
        granted_c = min(_cents(promo["discount_amount"]), remaining_c)
        if granted_c <= 0:
            continue
        remaining_c -= granted_c
        device_credit_c += granted_c
        applied.append({
            "id": promo["id"],
            "name": promo["name"],
            "type": "device_credit",
            "advertised": _dollars(_cents(promo["discount_amount"])),
            "applied": _dollars(granted_c),
            "capped": granted_c < _cents(promo["discount_amount"]),
        })

    # Divide once, at the end, so the monthly figure can't drift by a cent.
    net_device_c = remaining_c
    monthly_device_c = round(net_device_c / months) if months else net_device_c

    # --- recurring and one-time credits ------------------------------------
    monthly_credit_c = 0
    one_time_credit_c = 0
    for promo in promos:
        amount_c = _cents(promo["discount_amount"])
        if promo["discount_type"] == "monthly_credit":
            monthly_credit_c += amount_c
            applied.append({"id": promo["id"], "name": promo["name"],
                            "type": "monthly_credit",
                            "applied": _dollars(amount_c)})
        elif promo["discount_type"] == "bill_credit":
            one_time_credit_c += amount_c
            applied.append({"id": promo["id"], "name": promo["name"],
                            "type": "bill_credit",
                            "applied": _dollars(amount_c)})

    new_monthly_c = max(0, plan_c + monthly_device_c - monthly_credit_c)

    # --- receipt breakdown (sums exactly to new_monthly_total) -------------
    breakdown = [{
        "label": f'{PLANS[to_plan_id]["name"]} - {lines} line'
                 f'{"s" if lines != 1 else ""}',
        "amount": _dollars(plan_c),
    }]

    if new_device:
        detail = f'${_dollars(device_price_c):,.2f} device'
        if traded_c:
            detail += f' - ${_dollars(traded_c):,.2f} trade-in'
        if device_credit_c:
            detail += f' - ${_dollars(device_credit_c):,.2f} promo credit'
        breakdown.append({
            "label": f"{new_device} - {months} mo financing",
            "amount": _dollars(monthly_device_c),
            "detail": detail,
        })

    if monthly_credit_c:
        breakdown.append({"label": "Recurring promo credits",
                          "amount": -_dollars(monthly_credit_c)})

    return {
        "account_id": account_id,
        "customer_name": customer["name"],
        "from_plan": {"plan_id": from_plan_id,
                      "name": PLANS[from_plan_id]["name"],
                      "lines": current["lines"]},
        "to_plan": {"plan_id": to_plan_id,
                    "name": PLANS[to_plan_id]["name"],
                    "lines": lines},
        "previous_monthly_total": _dollars(previous_c),
        "new_monthly_total": _dollars(new_monthly_c),
        "monthly_delta": _dollars(new_monthly_c - previous_c),
        "direction": ("increase" if new_monthly_c > previous_c
                      else "decrease" if new_monthly_c < previous_c
                      else "no_change"),
        "device": None if not new_device else {
            "model": new_device,
            "retail_price": _dollars(device_price_c),
            "trade_in_device": trade_in_device,
            "trade_in_value": _dollars(traded_c),
            "promo_credit": _dollars(device_credit_c),
            "net_cost": _dollars(net_device_c),
            "monthly_payment": _dollars(monthly_device_c),
            "financing_months": months,
            "fully_covered": net_device_c == 0,
        },
        "promos_applied": applied,
        "one_time_credit": _dollars(one_time_credit_c),
        "breakdown": breakdown,
    }


if __name__ == "__main__":
    # Regression guard for the numbers in P5's deck. If this fails, the demo
    # and the slides have diverged - fix before pushing.
    demo = calculate_new_bill({
        "account_id": "5550192",
        "to_plan_id": "magenta_max",
        "new_device": "iPhone 16 Pro",
        "trade_in_device": "iPhone 13 Pro",
    })

    print(f'{demo["customer_name"]}: '
          f'${demo["previous_monthly_total"]} -> ${demo["new_monthly_total"]} '
          f'({demo["direction"]} of ${abs(demo["monthly_delta"])})\n')
    for line in demo["breakdown"]:
        print(f'  {line["label"]:38} ${line["amount"]:>8,.2f}')
        if line.get("detail"):
            print(f'  {"":38}  {line["detail"]}')
    print(f'\n  {"NEW MONTHLY TOTAL":38} ${demo["new_monthly_total"]:>8,.2f}')
    if demo["one_time_credit"]:
        print(f'  {"One-time bill credit":38} ${-demo["one_time_credit"]:>8,.2f}')
    print("\n  Promos applied:")
    for p in demo["promos_applied"]:
        flag = "  [CAPPED]" if p.get("capped") else ""
        print(f'    - {p["name"]}: ${p["applied"]:,.2f}{flag}')

    assert demo["new_monthly_total"] == 107.00, demo["new_monthly_total"]
    assert demo["previous_monthly_total"] == 85.00, demo["previous_monthly_total"]
    assert demo["monthly_delta"] == 22.00, demo["monthly_delta"]
    assert demo["device"]["fully_covered"], demo["device"]
    assert demo["device"]["monthly_payment"] == 0.00, demo["device"]

    # Derek: plan-only upgrade, no device. $70 -> $90 at 2 lines.
    derek = calculate_new_bill({"account_id": "5550271",
                                "to_plan_id": "magenta_max"})
    assert derek["new_monthly_total"] == 90.00, derek["new_monthly_total"]
    assert derek["device"] is None
    assert sum(b["amount"] for b in derek["breakdown"]) == 90.00

    # Tom: already on target plan, nothing changes.
    tom = calculate_new_bill({"account_id": "5550503"})
    assert tom["direction"] == "no_change", tom
    assert tom["monthly_delta"] == 0.00, tom

    # Every breakdown must sum to the stated monthly total.
    for acct in CUSTOMERS:
        for target in PLANS:
            b = calculate_new_bill({"account_id": acct, "to_plan_id": target})
            total = round(sum(x["amount"] for x in b["breakdown"]), 2)
            assert total == b["new_monthly_total"], (acct, target, total)

    print("\nALL ASSERTIONS PASSED")
