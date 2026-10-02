import json
from services.llm_service import LLMService
from prompts.brief_prompt import build_brief_prompt


class BriefAgent:
    def __init__(self):
        self.llm = LLMService()

    async def run(self, customer: dict) -> dict:
        prompt = build_brief_prompt(customer)
        raw = await self.llm.complete(prompt)
        try:
            # Strip markdown code fences if present
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(cleaned)
        except Exception:
            return {"raw": raw, "parse_error": True}
