# 02 · Architecture

> Two co-located processes. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The backend owns Agora tokens, the agent session, and a cascading Deepgram STT → Agora-managed OpenAI LLM → MiniMax TTS pipeline. No separate LLM service.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds OpenAI LLM + DeepgramSTT + MiniMaxTTS (managed, keyless)
                                 ▼
                              Agora ConvoAI Cloud
                                 │  user speech → Deepgram STT (managed)
                                 │  transcript → OpenAI LLM (Agora-managed, keyless)
                                 │  reply → MiniMax TTS (managed)
                                 ▼
                              User hears TTS voice; RTM transcript + metrics → web UI
```

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation and agent session lifecycle. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- No `llm/` service, no mock vendor, no public tunnel — the OpenAI LLM is Agora-managed (keyless).

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs.
2. Browser joins the RTC channel, then `POST /api/startAgent`; backend builds the vendor chain and starts an async agent session.
3. Agora routes user audio through Deepgram STT, then the Agora-managed OpenAI LLM, then MiniMax TTS back into the channel.
4. RTM delivers transcript + metrics to the web UI.
5. `POST /api/stopAgent { agentId }` ends the session.
6. `POST /api/updateInstructions { agentId, instructions }` swaps the running agent's system prompt without restarting.

## Why no `llm/` service

The instructions recipe uses Agora's **managed `OpenAI` vendor** (keyless). Agora calls OpenAI on your behalf — no intermediate proxy to expose. `OPENAI_API_KEY` is optional (set only for bring-your-own-key accounts).

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns `AsyncAgora` client, env, and the in-memory `_sessions` map keyed by `agent_id`. Holds `update_instructions()` that calls the Agora update API on a live session.
- **`instruction_config.py`** (`server/src/instruction_config.py`) — pure builders for system prompts, template variables, `max_tokens`, and update payloads. No `agora_agent` import, fully unit-testable.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed (set `AGENT_BACKEND_URL`).
- **`instruction_config.py` purity** — instruction building is isolated so prompt logic is testable without the SDK.
- **`turn_detection` on `AgoraAgent`** — this recipe uses the cascading vendor, so VAD is set as a top-level config on `AgoraAgent(...)`, not on an MLLM vendor.
- **Live instruction swap** — `POST /updateInstructions` calls `session.update(UpdateAgentsRequestProperties(...))` to replace the running system prompt mid-session.

## Related Deep Dives

- [instruction_config_and_update.md](L2/instruction_config_and_update.md) — full instruction builder details, template variables, live update flow.
- [session_lifecycle.md](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, transcript mapping.
