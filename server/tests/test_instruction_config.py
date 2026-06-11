import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import instruction_config as cfg  # noqa: E402


def test_reply_max_tokens():
    assert cfg.reply_max_tokens("short") <= 60
    assert cfg.reply_max_tokens("normal") >= 256


def test_build_instructions_short_is_terse_and_has_exit():
    text = cfg.build_instructions("short", "Bye now!")
    assert "one short sentence" in text.lower()
    assert "Bye now!" in text


def test_build_instructions_normal_has_exit():
    text = cfg.build_instructions("normal", "Bye now!")
    assert "Bye now!" in text


def test_build_template_variables():
    assert cfg.build_template_variables("Ada", "2026-06-11") == {
        "assistant_name": "Ada",
        "today": "2026-06-11",
    }


def test_build_update_system_messages():
    msgs = cfg.build_update_system_messages("You are a pirate.")
    assert msgs == [{"role": "system", "content": "You are a pirate."}]
