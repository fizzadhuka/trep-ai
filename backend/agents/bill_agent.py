"""Bill delta agent. [P1b]

Pricing is delegated entirely to services.bill_service — /bill-delta and P3's
final bill must never disagree on screen, so there is exactly one place that
does arithmetic. This agent's only job is wrapping those numbers in a sentence
a rep can read aloud.
"""

from __future__ import annotations

import re

from prompts.bill_delta_prompt import build_bill_delta_prompt
from services.bill_service import (
    CUSTOMERS,
    DEVICES,
    PLANS,
    BillError,
    calculate_new_bill,
    resolve_plan_id,
)
from services.llm_service import LLMService

# bill_service says "no_change"; the prompt and the API contract say "none".
_DIRECTION = {"no_change": "none"}

_ADD_LINE = re.compile(r"\badd(?:ing)?\s+(?:a\s+|an\s+|another\s+|(\d+)\s+)?lines?\b", re.I)
_DROP_LINE = re.compile(r"\b(?:remove|remov\w*|drop\w*|cancel\w*)\s+(?:a\s+|an\s+|(\d+)\s+)?lines?\b", re.I)


def parse_line_change(text: str) -> int:
    """Net line count change implied by free text (+n, -n, or 0).

    Live transcripts carry things like "can I add a line for my daughter",
    which is a bill question with no plan name in it. Without this the call
    would raise on plan resolution and the dashboard would show nothing.
    """
    if m := _ADD_LINE.search(text or ""):
        return int(m.group(1)) if m.group(1) else 1
    if m := _DROP_LINE.search(text or ""):
        return -(int(m.group(1)) if m.group(1) else 1)
    return 0


def find_plan_in_text(text: str) -> str | None:
    """Find a plan mentioned anywhere inside a sentence.

    bill_service.resolve_plan_id expects a bare plan name or id, which is what
    P4's dropdown sends. Speech does not arrive that way — "so could I switch
    to Go5G Plus" has the plan buried mid-sentence. Longest name first, so
    "Magenta MAX" is never shortened to "Magenta".
    """
    if not text:
        return None
    haystack = text.lower().replace("-", "_")
    candidates = sorted(
        ((p["name"].lower(), pid) for pid, p in PLANS.items()),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )
    for name, plan_id in candidates:
        if name in haystack or name.replace(" ", "_") in haystack:
            return plan_id
    return None


def find_device_in_text(text: str) -> str | None:
    """Find a purchasable device mentioned in a sentence.

    Longest name first: "iPhone 16 Pro" must not match as "iPhone 16", which
    is a different phone at a different price with a different trade-in value.
    """
    if not text:
        return None
    haystack = text.lower()
    for model in sorted(DEVICES, key=len, reverse=True):
        if model.lower() in haystack:
            return model
    return None


def _first_sentence(text: str) -> str:
    """Strip preambles, code fences, and quotes; keep one clean sentence."""
    cleaned = (text or "").strip().strip("`").strip()
    for line in cleaned.splitlines():
        line = line.strip().strip('"').strip()
        if not line:
            continue
        # Skip "Sure! Here's the explanation:" style openers.
        if line.endswith(":") and len(line) < 60:
            continue
        return line
    return cleaned


def _fallback_explanation(bill: dict) -> str:
    """Deterministic sentence for when the LLM is unavailable.

    Keeps /bill-delta usable if the gateway rate-limits or the network drops
    mid-demo. The numbers are already computed; only the phrasing is at risk.
    """
    name = bill["to_plan"]["name"]
    delta = abs(bill["monthly_delta"])
    total = bill["new_monthly_total"]

    if bill["direction"] == "no_change":
        return f"{name} costs the same as their current plan — still ${total:.2f} a month."
    verb = "adds" if bill["direction"] == "increase" else "saves"
    return (f"Switching to {name} {verb} ${delta:.2f} a month, "
            f"bringing the new total to ${total:.2f}.")


class BillAgent:
    def __init__(self):
        self.llm = LLMService()

    async def run(self, customer_id: str, current_plan: str, proposed_change: str) -> dict:
        """Bill delta for a proposed plan, device, and/or line-count change.

        Any combination is valid — "switch to Magenta MAX", "can I add a line",
        "how much for the iPhone 16 Pro", or all three in one sentence.

        Raises BillError for an unknown account, or when the text names no
        plan, no device, and no line change.
        """
        lines_delta = parse_line_change(proposed_change)
        new_device = find_device_in_text(proposed_change)

        try:
            to_plan_id = resolve_plan_id(proposed_change)
        except BillError:
            # Not a bare plan name — try to find one inside the sentence,
            # which is how it arrives from a live transcript.
            to_plan_id = find_plan_in_text(proposed_change)
            # Nothing actionable anywhere. Fine if they asked about a device or
            # lines; otherwise the caller genuinely passed something unusable.
            if to_plan_id is None and lines_delta == 0 and new_device is None:
                raise

        # A customer buying a phone almost always trades in the one in their
        # hand, and the trade-in is what makes the promo credit meaningful.
        # Asking them to state it out loud would be theatre — it's on the
        # account already.
        trade_in_device = None
        if new_device:
            customer = CUSTOMERS.get(str(customer_id), {})
            owned = customer.get("upgrade_eligibility", {}).get("current_device")
            if owned and owned in DEVICES[new_device]["trade_in_values"]:
                trade_in_device = owned

        bill = calculate_new_bill({
            "account_id": customer_id,
            "to_plan_id": to_plan_id,
            "lines_delta": lines_delta,
            "new_device": new_device,
            "trade_in_device": trade_in_device,
        })

        direction = _DIRECTION.get(bill["direction"], bill["direction"])

        prompt = build_bill_delta_prompt(
            current_plan=bill["from_plan"]["name"],
            proposed_plan=bill["to_plan"]["name"],
            lines=bill["from_plan"]["lines"],
            new_lines=bill["to_plan"]["lines"],
            current_total=bill["previous_monthly_total"],
            new_total=bill["new_monthly_total"],
            delta_dollars=bill["monthly_delta"],
            direction=direction,
            promos=bill["promos_applied"],
        )

        try:
            explanation = _first_sentence(await self.llm.complete(prompt))
            if not explanation:
                raise ValueError("empty explanation")
        except Exception:
            explanation = _fallback_explanation(bill)

        return {
            "customer_id": customer_id,
            "current_plan": bill["from_plan"]["name"],
            "proposed_plan": bill["to_plan"]["name"],
            "current_monthly_total": bill["previous_monthly_total"],
            "new_monthly_total": bill["new_monthly_total"],
            "delta_dollars": abs(bill["monthly_delta"]),
            "direction": direction,
            "explanation": explanation,
            # Extras for P4/P5 — safe to ignore.
            "lines": bill["from_plan"]["lines"],
            "new_lines": bill["to_plan"]["lines"],
            "device": bill["device"],
            "breakdown": bill["breakdown"],
            "promos_applied": bill["promos_applied"],
            "one_time_credit": bill["one_time_credit"],
        }
