from dataclasses import dataclass, field
from typing import Any

from . import config


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass
class LLMResponse:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any | None = None


class LLMConfigError(ValueError):
    pass


def generate(
    messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
) -> LLMResponse:
    provider = config.LLM_PROVIDER

    if provider == "gemini":
        return _generate_with_gemini(messages, tools)

    if provider in ("deepseek", "openai", "openai-compatible"):
        return _generate_with_openai_compatible(messages, tools)

    raise LLMConfigError(
        f"Unsupported LLM_PROVIDER '{provider}'. "
        "Use gemini, deepseek, openai, or openai-compatible."
    )


def validate_config() -> None:
    provider = config.LLM_PROVIDER
    model_name = config.get_llm_model_name()
    api_key = config.get_llm_api_key()

    if provider not in ("gemini", "deepseek", "openai", "openai-compatible"):
        raise LLMConfigError(
            f"Unsupported LLM_PROVIDER '{provider}'. "
            "Use gemini, deepseek, openai, or openai-compatible."
        )

    if not model_name:
        raise LLMConfigError(f"Missing model name for LLM_PROVIDER '{provider}'.")

    if _is_missing_secret(api_key):
        raise LLMConfigError(f"Missing API key for LLM_PROVIDER '{provider}'.")

    if provider == "openai-compatible" and not config.OPENAI_COMPATIBLE_BASE_URL:
        raise LLMConfigError(
            "OPENAI_COMPATIBLE_BASE_URL is required when LLM_PROVIDER=openai-compatible."
        )


def _generate_with_gemini(
    messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
) -> LLMResponse:
    if tools:
        raise LLMConfigError("Gemini tool calls are not wired yet.")

    from google import genai

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=config.GEMINI_MODEL_NAME,
        contents=_messages_to_prompt(messages),
    )
    return LLMResponse(text=response.text, raw=response)


def _generate_with_openai_compatible(
    messages: list[LLMMessage], tools: list[dict[str, Any]] | None = None
) -> LLMResponse:
    from openai import OpenAI

    client = OpenAI(
        api_key=config.get_llm_api_key(),
        base_url=config.get_llm_base_url(),
    )

    request: dict[str, Any] = {
        "model": config.get_llm_model_name(),
        "messages": [
            {"role": message.role, "content": message.content} for message in messages
        ],
    }
    if tools:
        request["tools"] = tools

    response = client.chat.completions.create(**request)
    message = response.choices[0].message

    tool_calls = []
    for tool_call in getattr(message, "tool_calls", None) or []:
        if not tool_call.function:
            continue
        tool_calls.append(
            ToolCall(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=tool_call.function.arguments,
            )
        )

    return LLMResponse(text=message.content, tool_calls=tool_calls, raw=response)


def _messages_to_prompt(messages: list[LLMMessage]) -> str:
    return "\n\n".join(
        f"{message.role.upper()}:\n{message.content}" for message in messages
    )


def _is_missing_secret(value: str | None) -> bool:
    if not value:
        return True
    normalized = value.strip().lower()
    return normalized.startswith("your_") or normalized in {"changeme", "todo"}
