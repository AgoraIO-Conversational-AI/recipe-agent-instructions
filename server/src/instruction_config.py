"""Pure builders for the instructions recipe — no `agora_agent` import, so they
are unit-testable without the SDK. agent.py wraps these into SDK objects."""
from typing import Dict, List


def reply_max_tokens(reply_style: str) -> int:
    return 40 if (reply_style or "normal").strip().lower() == "short" else 1024


def build_instructions(reply_style: str, exit_message: str) -> str:
    base = (
        "You are {{assistant_name}}, a friendly voice assistant. Today is {{today}}. "
        "Help the user with whatever they ask."
    )
    if (reply_style or "normal").strip().lower() == "short":
        base += " Always answer in one short sentence."
    base += f" When the user says goodbye, respond with exactly: {exit_message}"
    return base


def build_template_variables(assistant_name: str, today: str) -> Dict[str, str]:
    return {"assistant_name": assistant_name, "today": today}


def build_update_system_messages(new_instructions: str) -> List[Dict[str, str]]:
    """OpenAI-protocol system_messages payload for the Agora update API."""
    return [{"role": "system", "content": new_instructions}]
