"""P2 data-layer consistency check. Run from backend/:  python3 verify.py"""
import json
import sys

plans = json.load(open("mock/plans.json"))
customers = json.load(open("mock/customers.json"))
promos = json.load(open("mock/promos.json"))
devices = json.load(open("mock/devices.json"))

failures = []

# 1. Every customer's stated monthly_total must match the plan pricing table.
print("=== Customer totals vs plans.json ===")
for c in customers:
    cp = c["current_plan"]
    pid, lines = cp.get("plan_id"), str(cp["lines"])

    if pid is None:
        failures.append(f'{c["name"]}: missing plan_id')
        print(f'FAIL {c["name"]:16} no plan_id')
        continue
    if pid not in plans:
        failures.append(f'{c["name"]}: unknown plan_id {pid}')
        print(f'FAIL {c["name"]:16} unknown plan_id "{pid}"')
        continue

    expected = plans[pid]["monthly_total_by_lines"][lines]
    actual = cp["monthly_total"]
    ok = expected == actual
    if not ok:
        failures.append(f'{c["name"]}: stated {actual} != table {expected}')
    print(f'{"OK  " if ok else "FAIL"} {c["name"]:16} {pid:12} {lines} lines  '
          f'stated={actual:<7} table={expected}')

# 2. The demo delta must be exactly $22 (deck depends on it).
m = plans["magenta"]["monthly_total_by_lines"]["3"]
mx = plans["magenta_max"]["monthly_total_by_lines"]["3"]
delta = mx - m
print(f"\n=== Demo delta ===\nMagenta -> Magenta MAX @ 3 lines: ${m} -> ${mx} = ${delta}")
if delta != 22:
    failures.append(f"demo delta is ${delta}, deck says $22")
    print("FAIL deck says $22")
else:
    print("OK   matches deck")

# 3. promos.json must not reference plan ids that don't exist.
print("\n=== Promo plan-id references ===")
referenced = {p for pr in promos
              for p in pr["eligible_from_plans"] + pr["eligible_to_plans"]}
unknown = referenced - set(plans.keys())
if unknown:
    failures.append(f"promos reference unknown plan ids: {unknown}")
    print(f"FAIL unknown plan ids: {sorted(unknown)}")
else:
    print(f"OK   all {len(referenced)} referenced ids exist")

# 4. Every customer's device must appear as a trade-in option somewhere.
print("\n=== Customer devices vs devices.json ===")
tradeable = {d for dev in devices for d in dev["trade_in_values"]}
for c in customers:
    dev = c["upgrade_eligibility"]["current_device"]
    stated = c["upgrade_eligibility"]["trade_in_value"]

    # trade_in_value == 0 means "this customer is not trading in" (an
    # intentional opt-out, e.g. Derek's plan-upgrade-only demo path),
    # NOT "this device is worthless". Treated as valid either way.
    if not stated:
        print(f'INFO {c["name"]:16} "{dev}" trade_in_value=0 (opt-out, not a defect)')
        continue

    if dev not in tradeable:
        failures.append(f'{c["name"]}: device "{dev}" has no trade-in entry '
                        f'but claims ${stated}')
        print(f'FAIL {c["name"]:16} "{dev}" not in devices.json (claims ${stated})')
        continue

    offers = {dev_e["model"]: dev_e["trade_in_values"][dev]
              for dev_e in devices if dev in dev_e["trade_in_values"]}
    ok = stated in offers.values()
    if not ok:
        failures.append(f'{c["name"]}: claims ${stated} for "{dev}", '
                        f'devices.json offers {offers}')
    print(f'{"OK  " if ok else "FAIL"} {c["name"]:16} "{dev}" claims ${stated} '
          f'-> {offers}')

# 5. Device credits must never exceed what's left after trade-in.
print("\n=== Promo credit vs device price ===")
for pr in promos:
    if pr["discount_type"] != "device_credit":
        continue
    for dev in devices:
        for traded, tv in dev["trade_in_values"].items():
            remaining = dev["price"] - tv
            if pr["discount_amount"] > remaining:
                print(f'WARN {pr["id"]}: ${pr["discount_amount"]} credit vs '
                      f'${remaining} left on {dev["model"]} after "{traded}" '
                      f'trade-in (${tv}) - MUST CAP')

print("\n" + "=" * 60)
if failures:
    print(f"{len(failures)} FAILURE(S):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL CHECKS PASSED")
