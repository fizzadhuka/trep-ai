def build_brief_prompt(customer: dict) -> str:
    return f"""You are a T-Mobile rep assistant. Given a customer account object, produce a structured brief.

Return ONLY valid JSON, no markdown, no explanation. Exactly these fields:
{{
  "plan_summary": "one sentence describing their current plan and monthly cost",
  "upgrade_status": "one sentence on upgrade eligibility and trade-in value, including trade-in dollar amount if applicable",
  "bill_summary": "plain-language breakdown of what they pay and why",
  "open_issues": ["one-line status for each open issue, or empty array if none"],
  "pah_status": "one sentence: whether the person present is the account holder and authorized to make changes"
}}

Be concise — a rep reads this in seconds during a live customer interaction.
Customer data: {customer}"""
