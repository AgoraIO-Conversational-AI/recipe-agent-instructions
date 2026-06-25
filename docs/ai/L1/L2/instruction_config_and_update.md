# Deep Dive — Instruction Config and Live Update

> **When to Read This:** You are changing the system prompt, reply style, template variables, exit message, or the live runtime instruction swap via `POST /updateInstructions`. For the high-level picture, start at [02_architecture](../02_architecture.md).

`server/src/instruction_config.py` is a pure Python module (no `agora_agent` import). All prompt logic lives here so it can be tested without the SDK. `agent.py` imports and calls these builders when starting or updating a session.

## The builders

### `build_instructions(reply_style, exit_message) → str`

Assembles the system prompt from components:

```python
base = (
    "You are {{assistant_name}}, a friendly voice assistant. Today is {{today}}. "
    "Help the user with whatever they ask."
)
if reply_style == "short":
    base += " Always answer in one short sentence."
base += f" When the user says goodbye, respond with exactly: {exit_message}"
return base
```

`{{assistant_name}}` and `{{today}}` are placeholders — they are resolved by the Agora managed vendor at session start using `template_variables`. Do not substitute them in Python.

### `build_template_variables(assistant_name, today) → dict`

```python
return {"assistant_name": assistant_name, "today": today}
```

`today` is `datetime.date.today().isoformat()` computed in `Agent.start()`.

### `reply_max_tokens(reply_style) → int`

Returns `40` for `"short"`, `1024` for `"normal"` (or any other value). Controls the `max_tokens` field passed to `OpenAI(...)`.

### `build_update_system_messages(new_instructions) → list`

```python
return [{"role": "system", "content": new_instructions}]
```

Used by `update_instructions()` when assembling the `UpdateAgentsRequestPropertiesLlm` payload.

## How they are wired into the session (`agent.py`)

```python
llm = OpenAI(
    api_key=self.openai_api_key,          # None if not set (Agora-managed)
    model=self.openai_model,              # OPENAI_MODEL, default gpt-4o-mini
    system_messages=[{"role": "system", "content": build_instructions(self.reply_style, self.exit_message)}],
    template_variables=build_template_variables(self.assistant_name, today),
    max_tokens=reply_max_tokens(self.reply_style),
    greeting_message=self.greeting,
    temperature=0.7,
)
stt = DeepgramSTT(model="nova-3", language="en")
tts = MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")

agora_agent = AgoraAgent(client=..., turn_detection={...}, ...).with_stt(stt).with_llm(llm).with_tts(tts)
```

## Live instruction swap (`POST /updateInstructions`)

`Agent.update_instructions(agent_id, instructions)` swaps the system prompt on a running session:

```python
await session.update(
    UpdateAgentsRequestProperties(
        llm=UpdateAgentsRequestPropertiesLlm(
            system_messages=build_update_system_messages(instructions)
        )
    )
)
```

- Requires the session to be present in `self._sessions[agent_id]` (in-memory; not robust across backend restarts).
- The next agent turn uses the new prompt. No session restart needed.
- Does **not** update `template_variables` or `max_tokens` — only the system messages are swapped.

## Adding a new template variable

1. Add the variable key to `build_template_variables()` return dict.
2. Reference it as `{{my_var}}` in `build_instructions()` (or in update payloads).
3. Ensure `Agent.start()` passes the resolved value to `build_template_variables()`.
4. Verify: `cd server && pytest tests -v` (add a test asserting the new key appears in the dict).

## Related L1

- [02_architecture](../02_architecture.md) · [05_workflows](../05_workflows.md) · [06_interfaces](../06_interfaces.md) · [07_gotchas](../07_gotchas.md)
