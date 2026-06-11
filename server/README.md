# Agora Agent Backend — Instructions Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the instructions recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

- Generates Agora Token007 auth tokens for the browser client.
- Starts and stops agent sessions via `agora_agent`.
- Exposes `POST /updateInstructions` to swap the running agent's system prompt at
  runtime without restarting the session, using Agora's update API
  (`UpdateAgentsRequestProperties` + `UpdateAgentsRequestPropertiesLlm`).

The LLM stage uses Agora's **managed `OpenAI` vendor** — keyless by default, the
same model as Deepgram STT and MiniMax TTS. `OPENAI_API_KEY` is optional; set it
only if your Agora account requires a bring-your-own key. There is no separate
`llm/` service and no custom endpoint to expose or tunnel.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work on
this module directly:

```bash
cd server
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/server.py
```

## Environment

`server/.env.example` is the template. Required:

- `AGORA_APP_ID` — Agora project App ID.
- `AGORA_APP_CERTIFICATE` — Agora project App Certificate.
- `OPENAI_API_KEY` — optional. Agora manages the OpenAI key by default (keyless).
  Set it only if your Agora account requires a bring-your-own key.

Optional:

- `OPENAI_MODEL` — model name passed to the managed vendor (default `gpt-4o-mini`).
- `REPLY_STYLE` — `normal` (default) or `short` (terse, low `max_tokens`).
- `ASSISTANT_NAME` — injected as `{{assistant_name}}` in the system prompt
  (default `Ada`).
- `AGENT_EXIT_MESSAGE` — closing instruction appended to the system prompt.
- `AGENT_GREETING` — optional opening line override.
- `PORT` — HTTP listen port (default `8000`). Do not add this to
  `.env.example` — it would clobber the random port injected by
  `verify:local:fastapi`.

## API

- `GET /get_config` — returns Agora token + channel/UID config for the browser.
- `POST /startAgent` — starts an agent session; returns `agentId`.
- `POST /stopAgent` — stops a running agent session.
- `POST /updateInstructions` — swaps the live system prompt of a running session.
  Body: `{"agentId": "<id>", "instructions": "<new system prompt>"}`.

The repo-root `bun run verify:local:fastapi` exercises the start/stop/config
routes through the Next proxy using a fake agent (`scripts/run_fake_server.py`),
so no live Agora session is required for CI.
