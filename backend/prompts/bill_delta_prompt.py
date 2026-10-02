"""Prompt for plain-language bill change explanations. Owner: P1b."""


def build_bill_delta_prompt(
    *,
    current_plan: str,
    proposed_plan: str,
    lines: int,
    new_lines: int,
    current_total: float,
    new_total: float,
    delta_dollars: float,
    direction: str,
    promos: list[dict] | None = None,
) -> str:
    """Build the bill-delta explanation prompt.

    Every number the model is allowed to say is passed in explicitly. Without
    `new_total` in context the model invents one, which is how hallucinated
    dollar figures end up being read aloud to a customer.
    """
    promos = promos or []

    if direction == "none":
        change_line = "There is no change to their monthly bill."
    else:
        verb = "adds" if direction == "increase" else "saves"
        change_line = f"This {verb} ${abs(delta_dollars):.2f} per month."

    line_note = ""
    if new_lines != lines:
        delta_lines = new_lines - lines
        word = "line" if abs(delta_lines) == 1 else "lines"
        line_note = (
            f"\nLine count: {lines} → {new_lines} "
            f"({'adding' if delta_lines > 0 else 'removing'} {abs(delta_lines)} {word})."
        )

    promo_note = ""
    if promos:
        # bill_service returns {id, name, type, applied, ...}; earlier shapes
        # carried a description. Tolerate both rather than KeyError mid-demo.
        listed = "; ".join(
            p["name"] + (f" — {p['description']}" if p.get("description") else "")
            for p in promos
        )
        promo_note = f"\nPromotions already applied to these numbers: {listed}"

    return f"""You are a T-Mobile billing assistant. A retail rep will read your \
output aloud to the customer standing in front of them.

Write ONE sentence explaining the bill impact.

Facts (use these exact numbers, do not calculate anything yourself):
- Current plan: {current_plan}
- Proposed plan: {proposed_plan}
- Current monthly total: ${current_total:.2f}
- New monthly total: ${new_total:.2f}
- {change_line}{line_note}{promo_note}

Rules:
- Exactly one sentence. No preamble, no greeting, no sign-off.
- State the new monthly total explicitly.
- Use only the dollar figures given above.
- Plain language. No jargon, no bullet points, no markdown.
- Return the sentence only — no quotes around it.

Example of the right shape:
Upgrading to Magenta MAX adds $22 a month, bringing your new total to $107."""
