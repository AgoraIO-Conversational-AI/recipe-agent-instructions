# Agora Conversational AI — Instructions Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **instructions** recipe in the Agora Conversational AI recipes family. It
demonstrates how to configure the agent through system-prompt features, context
injection, and live runtime updates — all using Agora's **managed OpenAI vendor**.

This recipe is **zero-key**: it uses Agora's **managed OpenAI vendor** (keyless,
just like Deepgram STT and MiniMax TTS). `OPENAI_API_KEY` is **optional** — set
it only if your Agora account requires a bring-your-own key. There is no separate
LLM service to run or expose.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- Agora App ID + App Certificate (the [Agora CLI](https://github.com/AgoraIO/cli) makes this easy)

## Run It

```bash
# 1. Install dependencies
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>
agora project env write server/.env.local

# 3. Start the agent backend and web frontend
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak.

### Working from a clone

If you cloned this repo (rather than scaffolding via the Agora CLI), the steps
above are complete as written: `bun run setup` creates the Python venv and installs
web dependencies, then `bun run dev` brings up both services. You still need Agora
credentials in `server/.env.local` before a conversation can connect.

Services:

- Frontend — http://localhost:3000
- Backend — http://localhost:8000
- Mock LLM — n/a (Agora-managed)
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-instructions` on `v*` tags. It
runs the agent backend on **:8000 only** (no separate LLM port — OpenAI is
Agora-managed).

## Environment variables

Backend env file: [`server/.env.example`](server/.env.example).

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate |
| `OPENAI_API_KEY` | | — | Optional — Agora manages the OpenAI key by default; set only for bring-your-own key |
| `OPENAI_MODEL` | | `gpt-4o-mini` | OpenAI model name |
| `REPLY_STYLE` | | `normal` | `normal` or `short` (short → terse + low max_tokens) |
| `ASSISTANT_NAME` | | `Ada` | Injected as `{{assistant_name}}` in the system prompt |
| `AGENT_EXIT_MESSAGE` | | `Thanks for chatting — goodbye!` | Closing instruction appended to the system prompt |
| `AGENT_GREETING` | | built-in | Optional opening line override |
| `AGENT_BACKEND_URL` (web deploy) | ✅ | — | Required when deploying `web` separately |

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials check

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session (managed OpenAI vendor)
                          ▼
                       Agora ConvoAI Cloud
                          │  Deepgram STT (managed)
                          │  OpenAI LLM (Agora-managed, keyless)
                          │  MiniMax TTS (managed)
                          ▼
                       RTM transcript / metrics → web UI
```

The browser only ever calls Next `/api/*`, which rewrites to the agent backend.
The agent backend owns Agora tokens and agent lifecycle. LLM calls go through
Agora's managed OpenAI integration — no separate endpoint to expose. See
[ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **Next.js** web client (:3000) that drives the RTC/RTM lifecycle and only
  ever calls `/api/*`.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the
  agent session lifecycle.
- The `/api/get_config` · `/api/startAgent` · `/api/stopAgent` contract between
  the web client and the backend (Next rewrites, no Route Handlers).
- **Agora-managed keyless OpenAI** — the same zero-key model used for Deepgram STT
  and MiniMax TTS. Agora provisions OpenAI access on your behalf; `OPENAI_API_KEY`
  is optional (set it only if your Agora account requires a bring-your-own key).
- **`template_variables`** — inject `{{assistant_name}}` and `{{today}}` into the
  system prompt at agent-start time.
- **`REPLY_STYLE`** — set to `short` for terse one-sentence answers (low
  `max_tokens`) or `normal` (default) for fuller responses.
- **`POST /updateInstructions`** — swap the running agent's system prompt at any
  time via Agora's update API without restarting the session.
- **`AGENT_EXIT_MESSAGE`** — append a closing instruction so the agent delivers a
  consistent goodbye line when the user ends the conversation.

## How It Works

1. The browser calls `/api/get_config`, which Next rewrites to the backend; the
   backend mints an Agora token from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   starts an agent session using the managed `OpenAI` vendor with the configured
   system prompt (including `template_variables` and `REPLY_STYLE` settings).
3. The user speaks. Agora runs STT (Deepgram nova-3), then sends the transcript
   to the Agora-managed OpenAI endpoint.
4. OpenAI processes the request using the configured `OPENAI_MODEL` and returns a
   response. The `REPLY_STYLE` setting controls verbosity (`short` caps
   `max_tokens`; `normal` allows fuller replies).
5. Agora runs TTS (MiniMax) on the reply and plays it back in the channel.
6. While a session is running, you can swap the agent's system prompt without
   restarting — call `POST /updateInstructions` with the agent ID and new
   instructions:

   ```bash
   curl -X POST http://localhost:8000/updateInstructions \
     -H "Content-Type: application/json" \
     -d '{"agentId": "<agent_id_from_startAgent>", "instructions": "You are a pirate. Arr!"}'
   ```

   The next agent turn will use the new prompt. This is the key capability this
   recipe demonstrates: a live configurable agent personality driven entirely by
   system-prompt features, with no separate LLM service to maintain.
7. `AGENT_EXIT_MESSAGE` appends a closing instruction to the system prompt so the
   agent delivers a consistent goodbye line when the conversation ends.
8. `/api/stopAgent` ends the session.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle and UI.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle, managed OpenAI vendor.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent starts but never responds | Check `OPENAI_MODEL` is a valid model name. If your Agora account requires a key, ensure `OPENAI_API_KEY` is set in `server/.env.local`. |
| Local calls fail / hang under a proxy | Configure your proxy to route `127.0.0.1` and `localhost` DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
