from core.llm.llm_request_handler import send_prompt_to_llm_async

__all__ = ["LLMClient", "send_prompt_to_llm_async"]


class LLMClient:
    """Helpers for building LLM chat requests."""

    @staticmethod
    def create_messages(
        user_content: str,
        system_content: str | None = None,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})
        return messages
