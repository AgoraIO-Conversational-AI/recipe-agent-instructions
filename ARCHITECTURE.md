# Architecture — Instructions Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle. The LLM is
Agora-managed (keyless) — there is no separate LLM endpoint.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs
  │  POST /api/startAgent           → start agent session
  │  POST /api/updateInstructions   → swap system prompt at runtime
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with OpenAI(model=..., template_variables={...})  [keyless]
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed)
  │  text → OpenAI LLM (Agora-managed, keyless)
  │  response → MiniMax TTS (managed)
  ▼
Agora ConvoAI Cloud → RTM transcript / metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

`POST /api/updateInstructions { agentId, instructions }` calls the Agora update
API to swap the running agent's system prompt without restarting the session.

## Why one backend (no llm/ service)

Unlike the custom-llm recipe, this recipe uses Agora's **managed OpenAI vendor**
(keyless, the same model as Deepgram STT and MiniMax TTS). Agora cloud calls
OpenAI on your behalf with no key required — there is no intermediate proxy you
need to expose. Everything stays inside `server/`. `OPENAI_API_KEY` is optional
and only needed if your Agora account requires a bring-your-own key.

## Key features wired in agent.py

| Feature | Implementation |
| --- | --- |
| Template variables | `OpenAI(template_variables={"assistant_name": ..., "today": ...})` |
| Reply length control | `REPLY_STYLE=short` → `max_tokens=40`; `normal` → `max_tokens=1024` |
| Live instruction swap | `session.update(UpdateAgentsRequestProperties(llm=...))` |
| Exit message | Appended to system prompt as a closing instruction |

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session |
| `/stopAgent` | POST | Stop the agent by `agent_id` |
| `/updateInstructions` | POST | Swap system prompt on a running session |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → OpenAI: Agora-managed (keyless). `OPENAI_API_KEY` is forwarded only
  if set (bring-your-own key accounts).
