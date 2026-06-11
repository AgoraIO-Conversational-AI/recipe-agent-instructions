# Agora Conversational AI — Instructions Recipe (Python)

The **instructions** recipe in the Agora Conversational AI recipes family. It
demonstrates how to configure the agent through system-prompt features, context
injection, and live runtime updates — all using Agora's **managed OpenAI vendor**.

This recipe is **zero-key**: it uses Agora's **managed OpenAI vendor** (keyless,
just like Deepgram STT and MiniMax TTS). `OPENAI_API_KEY` is **optional** — set
it only if your Agora account requires a bring-your-own key. There is no separate
`llm/` service to run or expose.

## What this recipe demonstrates

- **`template_variables`** — inject `{{assistant_name}}` and `{{today}}` into the
  system prompt at agent-start time.
- **`REPLY_STYLE`** — set to `short` for terse one-sentence answers (low
  `max_tokens`) or `normal` (default) for fuller responses.
- **`POST /updateInstructions`** — swap the running agent's system prompt at any
  time via Agora's update API without restarting the session.
- **`AGENT_EXIT_MESSAGE`** — append a closing instruction so the agent delivers a
  consistent goodbye line when the user ends the conversation.

## Prerequisites

- [Python 3.8+](https://www.python.org/)
- [Bun](https://bun.sh/)
- Agora App ID + App Certificate (the [Agora CLI](https://github.com/AgoraIO/cli) makes this easy)

## Run it

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

## Live instruction swap (example)

While a session is running, swap the agent's system prompt without restarting:

```bash
curl -X POST http://localhost:8000/updateInstructions \
  -H "Content-Type: application/json" \
  -d '{"agentId": "<agent_id_from_startAgent>", "instructions": "You are a pirate. Arr!"}'
```

The next agent turn will use the new prompt.

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

## Project structure

```
recipe-agent-instructions/
├── server/   # Agent backend (:8000) — tokens, agent lifecycle, OpenAI vendor
│   ├── src/{server.py, agent.py, instruction_config.py}
│   └── tests/test_instruction_config.py
├── web/      # Next.js frontend (:3000)
└── package.json
```

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

## Zero-key design

This recipe uses Agora's **managed OpenAI vendor** — the same keyless model used
for Deepgram STT and MiniMax TTS. Agora provisions the OpenAI access on your
behalf; you do not need to supply `OPENAI_API_KEY` to run the recipe. If your
Agora account requires a bring-your-own OpenAI key, set `OPENAI_API_KEY` in
`server/.env.local` and it will be forwarded automatically.

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

## Troubleshooting

| Problem | Fix |
| --- | --- |
| Agent starts but never responds | Check `OPENAI_MODEL` is a valid model name. If your Agora account requires a key, ensure `OPENAI_API_KEY` is set in `server/.env.local`. |
| Local calls fail / hang under a proxy | Configure your proxy to route `127.0.0.1` and `localhost` DIRECT. |

## License

MIT
