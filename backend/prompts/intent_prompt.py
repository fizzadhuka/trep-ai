def build_intent_prompt(transcript: str) -> str:
    return f"""You are a T-Mobile rep assistant listening to a live customer conversation.

Given this transcript chunk, identify if the customer is asking about:
- A specific plan (name it)
- A device upgrade (name the device if mentioned)
- Adding or removing a line
- A trade-in
- A promo or discount
- A billing question

Return ONLY valid JSON with no explanation or markdown:
{{
  "topic": "plan_upgrade",
  "details": {{"plan_name": "Magenta MAX"}},
  "action": "fetch_plan",
  "confidence": 0.92
}}

topic must be one of: "plan_upgrade", "device_inquiry", "add_line", "trade_in", "promo", "billing", "none"
action must be one of: "fetch_plan", "fetch_device", "calculate_delta", "fetch_promo", "none"
confidence is a float 0.0–1.0

If no clear topic is detected, or confidence <= 0.7, return:
{{"topic": "none", "details": {{}}, "action": "none", "confidence": 0.0}}

Transcript: {transcript}"""
