# Architecture — Instructions Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens, agent lifecycle, and the
OpenAI API key. The LLM is Agora-managed — there is no separate LLM endpoint.

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
  │  builds session with OpenAI(api_key=OPENAI_API_KEY, template_variables={...})
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed)
  │  text → OpenAI LLM via OPENAI_API_KEY (managed by Agora)
  │  response → MiniMax TTS (managed)
  ▼
Agora ConvoAI Cloud → RTM transcript / metrics → web UI
```

`POST /api/stopAgent { agentId }` ends the session.

`POST /api/updateInstructions { agentId, instructions }` calls the Agora update
API to swap the running agent's system prompt without restarting the session.

## Why one backend (no llm/ service)

Unlike the custom-llm recipe, this recipe uses Agora's **managed OpenAI vendor**.
Agora cloud calls OpenAI directly using the `OPENAI_API_KEY` you supply — there is
no intermediate proxy you need to expose. Everything stays inside `server/`.

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
- Agora cloud → OpenAI: `OPENAI_API_KEY` (passed through Agora's managed vendor).
