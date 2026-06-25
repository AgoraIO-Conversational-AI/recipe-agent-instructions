# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Change the system prompt / persona

1. Edit `build_instructions(reply_style, exit_message)` in `server/src/instruction_config.py`.
2. To add new template variables (e.g. `{{user_name}}`), extend `build_template_variables()` and pass the new key in `Agent.start()`.
3. Verify: `cd server && pytest tests -v` (tests assert prompt content and template-variable shape).

## Change `REPLY_STYLE` behavior

1. `reply_max_tokens(reply_style)` controls `max_tokens`; edit it in `instruction_config.py` to add new styles or adjust token caps.
2. `build_instructions` adds the terse phrasing for `short`; edit there if the verbosity instruction needs changing.
3. Verify: `cd server && pytest tests -v`.

## Change the greeting or exit message

1. Greeting: set `AGENT_GREETING` (env) or edit the default in `Agent.__init__`.
2. Exit message: set `AGENT_EXIT_MESSAGE` (env) or edit the default in `Agent.__init__`; it is appended by `build_instructions`.
3. Verify: `bun run verify:backend` (compile).

## Change the model or STT/TTS

1. Model: set `OPENAI_MODEL` (default `gpt-4o-mini`).
2. STT/TTS: edit the `DeepgramSTT` / `MiniMaxTTS` constructors in `Agent.start()`.
3. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Live instruction swap (`POST /updateInstructions`)

This route already exists. To trigger it in code or from the shell:

```bash
curl -X POST http://localhost:8000/updateInstructions \
  -H "Content-Type: application/json" \
  -d '{"agentId": "<id>", "instructions": "You are a pirate. Arr!"}'
```

The next agent turn will use the new system prompt. The session stays running — no restart needed.

## Run / debug locally

```bash
bun run dev              # both processes
bun run doctor:local     # check creds + .env.local before a live call
```

## Verify before finishing

| Change touches…              | Run                                                                 |
| ---------------------------- | ------------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                                 |
| Backend logic / prompts      | `bun run verify:backend` + `cd server && pytest tests -v`            |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`    |
| Anything end-to-end (local)  | `bun run verify:local`                                               |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` (or any reachable FastAPI host); the published backend-only image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-instructions` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.

## Related Deep Dives

- [instruction_config_and_update.md](L2/instruction_config_and_update.md) — full instruction builder and live update details.
- [session_lifecycle.md](L2/session_lifecycle.md) — client-side join/renewal/teardown.
