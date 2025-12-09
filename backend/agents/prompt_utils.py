"""
Shared prompt loading and LangChain executor helpers.

This keeps prompt handling consistent across agents and avoids duplicating
LangChain bootstrap logic. The helpers are defensive: if the runtime does not
have LLM credentials or LangChain extras installed, they degrade gracefully so
agents can still operate with deterministic fallbacks.
"""

import os
import json
from pathlib import Path
from typing import Iterable, Optional, Type, Any


def load_prompt(section_header: str) -> str:
    """
    Load a prompt section from docs/system-prompts.md.

    Args:
        section_header: Title of the section to locate.

    Returns:
        The prompt text if found, otherwise a placeholder string.
    """
    prompt_path = Path(__file__).resolve().parents[1] / "docs" / "system-prompts.md"
    try:
        content = prompt_path.read_text(encoding="utf-8")
    except OSError:
        return f"{section_header} prompt (missing docs/system-prompts.md)"

    # Simple section extraction: split by headers and match case-insensitively.
    lowered = content.lower()
    marker = section_header.lower()
    if marker not in lowered:
        return f"{section_header} prompt"

    start_idx = lowered.index(marker)
    snippet = content[start_idx:]
    fence = "```"
    if fence not in snippet:
        return f"{section_header} prompt"
    first_fence = snippet.index(fence) + len(fence)
    second_fence = snippet.find(fence, first_fence)
    if second_fence == -1:
        return f"{section_header} prompt"
    return snippet[first_fence:second_fence].strip()


def build_agent_executor(
    prompt: str,
    tools: Optional[Iterable[object]] = None,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.2,
):
    """
    Construct a LangChain AgentExecutor with a chat model and provided tools.

    The import is local to keep optional dependency surfaces light. If LangChain
    or an OpenAI-compatible chat model is unavailable, returns None so callers
    can fall back to deterministic logic without raising.
    """
    if not _ensure_openai_api_key():
        return None
    try:
        from langchain.agents import AgentExecutor, create_openai_tools_agent
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except Exception:
        return None

    model = ChatOpenAI(model=model_name, temperature=temperature)
    tools_list = list(tools or [])
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", prompt),
            ("human", "{input}"),
        ]
    )
    agent = create_openai_tools_agent(model, tools_list, prompt_template)
    return AgentExecutor(agent=agent, tools=tools_list)


def invoke_structured(
    agent_executor: Any,
    input_text: str,
    model: Type[Any]
):
    """
    Invoke agent executor and parse output through a Pydantic model.
    Returns None on any failure so caller can fallback.
    """
    if not agent_executor:
        return None
    try:
        result = agent_executor.invoke({"input": input_text})
        payload = result.get("output") if isinstance(result, dict) else result
        if isinstance(payload, str):
            payload = payload.strip()
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                pass
        return model.model_validate(payload)
    except Exception:
        return None


def _ensure_openai_api_key() -> bool:
    """
    Load OPENAI_API_KEY from environment or project .env if present.
    """
    if os.getenv("OPENAI_API_KEY"):
        return True

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return False

    try:
        try:
            from dotenv import load_dotenv  # type: ignore
        except Exception:
            load_dotenv = None  # type: ignore

        if load_dotenv:
            load_dotenv(env_path)
        else:
            # Minimal manual parse
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if not line or line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == "OPENAI_API_KEY":
                    os.environ.setdefault("OPENAI_API_KEY", value.strip().strip('"').strip("'"))
                    break
    except OSError:
        return False

    return bool(os.getenv("OPENAI_API_KEY"))
