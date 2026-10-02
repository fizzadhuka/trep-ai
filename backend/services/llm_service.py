import os
import asyncio
import httpx
import anthropic


class LLMService:
    """Thin wrapper around Anthropic Claude."""

    def __init__(self):
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        kwargs = {"api_key": os.getenv("ANTHROPIC_API_KEY", "")}
        if base_url:
            kwargs["base_url"] = base_url
            # T-Mobile proxy uses a corporate cert not trusted by the local store
            kwargs["http_client"] = httpx.Client(verify=False)
        self.client = anthropic.Anthropic(**kwargs)
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    async def complete(self, prompt: str, system: str = "") -> str:
        messages = [{"role": "user", "content": prompt}]
        # Run sync SDK call in a thread so it doesn't block the event loop
        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=1024,
            system=system or "You are a helpful T-Mobile rep assistant.",
            messages=messages,
        )
        return response.content[0].text
