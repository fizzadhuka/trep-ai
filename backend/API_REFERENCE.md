# T-Rep AI — Backend API Reference

Owner: **P2** (data layer). Every example below is a real captured response, not a sketch.

Base URL: `http://localhost:8000` · Interactive docs: `http://localhost:8000/docs`

```bash
cd backend && source venv/bin/activate && uvicorn main:app --reload
```

---

## Read this first: three rules that will save you debugging time

**1. Look plans up by `plan_id`, never by display name.**
IDs are `essentials`, `magenta`, `magenta_max`, `go5g_plus` — underscores, not hyphens or spaces. Every customer object carries `current_plan.plan_id` as the join key.

**2. Never compute a price yourself.** Call `calculate_new_bill()`. If two components do their own arithmetic they will eventually disagree on screen while a judge watches.

**3. `monthly_total_by_lines` is a lookup table, not a formula.** A 3-line Magenta account costs `monthly_total_by_lines["3"]` = `$85`. Don't sum per-line rates — there are none.

---

## Demo numbers — locked, do not change

| | |
|---|---|
| Demo customer | Maria Gonzalez, account `5550192` |
| Current | Magenta, 3 lines, **$85.00/mo** |
| Target | Magenta MAX, 3 lines, **$107.00/mo** |
| Delta | **+$22.00/mo** |
| Device | **iPhone 16 Pro** ($999) — *not* base iPhone 16 |
| Trade-in | iPhone 13 Pro → **$320** |
| Promo credit | **$679** (advertised $830, capped at balance owed) |
| Net device cost | **$0.00** |
| One-time credit | **$100** (Magenta MAX Upgrade Credit) |

`verify.py` asserts the $22 delta. If it fails, the data and the deck have diverged.

The iPhone 16 Pro detail matters: a base iPhone 16 gives only **$280** for the same trade-in, which breaks the $320 figure in the deck.

---

## Test accounts

| Account | Name | Plan | Lines | Monthly | Scenario |
|---|---|---|---|---|---|
| `5550192` | Maria Gonzalez | Magenta | 3 | $85 | **Primary demo.** Upgrade + trade-in + open billing dispute. Is the PAH. |
| `5550271` | Derek Wu | Magenta | 2 | $70 | Backup demo. Plan-only upgrade, no trade-in. |
| `5550388` | Jake Patel | Essentials | 2 | $60 | **PAH flow.** Priya Patel is the PAH and is *not* present. |
| `5550412` | Sandra Okafor | Magenta MAX | 3 | $107 | Failed payment on file, still upgrade-eligible. |
| `5550503` | Tom Reyes | Magenta MAX | 2 | $90 | Not upgrade-eligible (5 months in). |

⚠️ **Tom is not on the top tier.** Go5G Plus outranks Magenta MAX, so BillExplorer will offer him an upgrade. If his scenario needs to be "nothing to upgrade," move him to `go5g_plus`.

---

# P2 endpoints — stable, use freely

## `GET /customer/{account_id}`

Full customer record. **404** with the list of known accounts if not found.

```json
{
  "account_id": "5550192",
  "name": "Maria Gonzalez",
  "phone": "555-019-2000",
  "primary_holder": { "name": "Maria Gonzalez", "is_present": true },
  "current_plan": {
    "plan_id": "magenta",
    "name": "Magenta",
    "monthly_total": 85.0,
    "lines": 3
  },
  "upgrade_eligibility": {
    "eligible": true,
    "current_device": "iPhone 13 Pro",
    "months_in": 18,
    "trade_in_value": 320.0
  },
  "open_issues": [
    { "type": "billing_dispute", "description": "Overcharge from June cycle", "status": "open" }
  ],
  "authorized_users": ["Maria Gonzalez"],
  "last_interaction": "2026-06-14"
}
```

**PAH check:** the visiting person is authorized if their name is in `authorized_users`. For Jake (`5550388`), `primary_holder.is_present` is `false` and `authorized_users` is `["Priya Patel"]` — that's what triggers PAHPanel.

**`trade_in_value` semantics:** market value of the device they own. `0` means "not trading in" (Derek), *not* "worthless."

## `GET /customer/search?q=`

Substring match on name, phone, or account id. Returns up to 10 full customer objects. Powers CustomerLookup — accepts a partial phone number.

## `GET /customer/plans`

Plan catalog for BillExplorer's dropdown. Ordered by `tier` ascending.

```json
[
  { "plan_id": "essentials",  "name": "Essentials",  "tier": 1,
    "monthly_total_by_lines": {"1":45,"2":60,"3":70,"4":80,"5":90},
    "features": ["5G access", "Unlimited talk, text, data"] },
  { "plan_id": "magenta",     "name": "Magenta",     "tier": 2,
    "monthly_total_by_lines": {"1":50,"2":70,"3":85,"4":100,"5":115}, "features": [...] },
  { "plan_id": "magenta_max", "name": "Magenta MAX", "tier": 3,
    "monthly_total_by_lines": {"1":65,"2":90,"3":107,"4":124,"5":141}, "features": [...] },
  { "plan_id": "go5g_plus",   "name": "Go5G Plus",   "tier": 4,
    "monthly_total_by_lines": {"1":75,"2":105,"3":125,"4":145,"5":165}, "features": [...] }
]
```

## `GET /customer/promotions`

| Param | Type | Default | Notes |
|---|---|---|---|
| `from_plan` | str | `""` | plan_id **or** display name **or** hyphenated |
| `to_plan` | str | `""` | same |
| `has_trade_in` | bool | `true` | `false` filters out device-credit promos |
| `lines` | int | `0` | line count *after* the change; `0` skips the check |

Returns `[]` — never an error — for an unknown plan. An empty promo list is a valid answer.

```
GET /customer/promotions?from_plan=magenta&to_plan=magenta_max&lines=3
→ ["iphone16-tradein" ($830 device_credit), "magenta-max-upgrade" ($100 bill_credit)]
```

**Do not display `discount_amount` as the amount the customer receives.** It's the advertised ceiling. The applied figure comes from `calculate_new_bill().promos_applied[].applied`.

## `GET /customer/trade-in/{device_model}`

The path param is the phone being **traded in**, not the one being bought. Value varies by target device.

```json
{
  "device": "iPhone 13 Pro",
  "eligible": true,
  "offers": { "iPhone 16 Pro": 320, "iPhone 16": 280 },
  "best_value": 320,
  "best_toward": "iPhone 16 Pro"
}
```

Unknown or non-tradeable device returns `eligible: false`, `offers: {}`, `best_value: 0`. Matching is exact and case-insensitive — `iPhone 16` will **not** match `iPhone 16 Pro`.

---

# `calculate_new_bill()` — the money function

**Not an HTTP endpoint.** Import it. P1's `/bill-delta` and P3's execution engine both call this.

```python
from services.bill_service import calculate_new_bill

bill = calculate_new_bill({
    "account_id": "5550192",        # required
    "to_plan_id": "magenta_max",    # default: their current plan
    "new_device": "iPhone 16 Pro",  # omit for plan-only change
    "trade_in_device": "iPhone 13 Pro",
    "lines_delta": 0,               # +1 adds a line
    "financing_months": 24,
})
```

Returns:

```python
{
  "account_id": "5550192",
  "customer_name": "Maria Gonzalez",
  "from_plan": {"plan_id": "magenta", "name": "Magenta", "lines": 3},
  "to_plan":   {"plan_id": "magenta_max", "name": "Magenta MAX", "lines": 3},
  "previous_monthly_total": 85.0,
  "new_monthly_total": 107.0,
  "monthly_delta": 22.0,
  "direction": "increase",          # "increase" | "decrease" | "no_change"
  "device": {
      "model": "iPhone 16 Pro", "retail_price": 999.0,
      "trade_in_device": "iPhone 13 Pro", "trade_in_value": 320.0,
      "promo_credit": 679.0, "net_cost": 0.0,
      "monthly_payment": 0.0, "financing_months": 24,
      "fully_covered": True,
  },
  "promos_applied": [
      {"id": "iphone16-tradein", "name": "iPhone 16 Trade-In Deal",
       "type": "device_credit", "advertised": 830.0, "applied": 679.0, "capped": True},
      {"id": "magenta-max-upgrade", "name": "Magenta MAX Upgrade Credit",
       "type": "bill_credit", "applied": 100.0},
  ],
  "one_time_credit": 100.0,
  "breakdown": [
      {"label": "Magenta MAX - 3 lines", "amount": 107.0},
      {"label": "iPhone 16 Pro - 24 mo financing", "amount": 0.0,
       "detail": "$999.00 device - $320.00 trade-in - $679.00 promo credit"},
  ],
}
```

**`breakdown` always sums exactly to `new_monthly_total`** — asserted across all 5 customers × 4 plans. Render it directly in FinalBillCard.

**`one_time_credit` is not in `breakdown`** and does not affect the monthly total. Show it as a separate line, e.g. *"plus $100 back on the first bill."* Spreading it monthly would make Maria $102.83 and contradict the deck.

**`capped: true`** means the promo's advertised amount exceeded the balance owed. Display `applied`, not `advertised`.

Raises `BillError` (a `ValueError`) on unknown account, plan, or device. Catch it and return a 4xx.

### Also importable from `services.bill_service`

| | |
|---|---|
| `resolve_plan_id(value)` | Accepts `magenta_max`, `Magenta MAX`, or `magenta-max` → `"magenta_max"`. Raises `BillError`. |
| `plan_monthly_cents(plan_id, lines)` | Integer cents. Extrapolates past 5 lines using marginal cost. |
| `trade_in_offers(device_model)` | `{target_device: value}` for a device the customer owns. |
| `PLANS`, `CUSTOMERS`, `PROMOS`, `DEVICES` | Preloaded dicts. `CUSTOMERS` keyed by account_id, `DEVICES` by model. |

---

# Other owners' endpoints

Shapes below are current as of this writing — confirm with the owner before building against them.

| Endpoint | Owner | Notes |
|---|---|---|
| `GET /brief/{customer_id}` | P1 | LLM-generated brief |
| `POST /bill-delta` | P1 | Body: `{customer_id, current_plan, proposed_change}`. Plan fields accept display names. Falls back to a deterministic sentence if the LLM fails, so it won't 500 mid-demo. |
| `POST /intent` | P1 | Body: `{transcript, customer_id}` |
| `POST /pah-check` | P1 | Reads `authorized_users` |
| `GET /execute/steps` | P3 | 6 steps; step 3 carries `error_step: true` |
| `POST /execute/simulate` | P3 | REST fallback for the WebSocket |
| `WS /ws/execute` | P3 | Streams step status |

`/execute/steps` today:

```json
[
  {"id": 1, "name": "Verifying account identity",  "duration_ms": 1000},
  {"id": 2, "name": "Confirming trade-in value",   "duration_ms": 1200},
  {"id": 3, "name": "Applying upgrade promotion",  "duration_ms": 800, "error_step": true},
  {"id": 4, "name": "Processing plan change",      "duration_ms": 1500},
  {"id": 5, "name": "Entering order into DASH",    "duration_ms": 1000},
  {"id": 6, "name": "Generating updated bill",     "duration_ms": 800}
]
```

---

## Self-tests — run before you push

```bash
cd backend
python3 verify.py                   # cross-file consistency + $22 delta
python3 services/bill_service.py    # bill math + deck numbers
```

`verify.py` prints `WARN ... MUST CAP` lines. **These are expected.** They document where an uncapped credit *would* exceed the balance; `bill_service` caps it. If someone removes the cap, those lines are the trail back to why it existed.

## Gotchas

**Route order in `routes/customer.py` is load-bearing.** FastAPI matches in declaration order, so every static path must stay above `/{customer_id}`. Add new routes above the marker comment — below it they'll be swallowed and 404 as "customer not found."

**CORS** allows `http://localhost:5173` by default. Override with `CORS_ORIGINS` in `.env` (comma-separated) if Vite picks another port.

**`schemas/models.py` is a shared file** where the agreed tree specified five. Conflict hotspot — coordinate before editing.
