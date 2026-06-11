# Agent Development Guide

For coding agents working in this repository. This is the **instructions** recipe
(`Recipe Role: instructions`) in the Agora Conversational AI recipes family,
derived from the base `agent-quickstart-python` template.

## System shape

- **`server/`** — Python FastAPI agent backend (:8000). Owns Agora token
  generation and agent session lifecycle. Uses Agora's managed `OpenAI` vendor.
  SDK: `agora-agents>=2.0.0` (`import agora_agent`).
  - `server/src/instruction_config.py` — pure builders for system prompts,
    template variables, max_tokens, and update payloads (no SDK import, fully
    unit-testable).
  - `server/tests/` — pytest unit tests for `instruction_config`.
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend (:3000).
- Auth: Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.
- **Zero-key**: OpenAI is Agora-managed (keyless, like Deepgram/MiniMax).
  `OPENAI_API_KEY` is optional — set it only if your Agora account requires a
  bring-your-own key.

## Routing / ownership

- UI and RTC/RTM lifecycle live in `web/`.
- Browser-facing `/api/*` paths are Next rewrites (`web/next.config.ts`) to the
  agent backend; do not add `web/app/api/**/route.ts` for agent/token logic.
- Token generation and agent lifecycle live in `server/src/`.
- Instruction builders (pure functions) live in `server/src/instruction_config.py`.

## Supported modes

- **Local:** `bun run dev` starts `server` (:8000) and `web` (:3000). The web app
  calls `/api/*`; Next rewrites to `AGENT_BACKEND_URL=http://localhost:8000`. No
  tunnel needed — the LLM is Agora-managed.
- **Deploy:** deploy `web` (Next) + `server` (reachable FastAPI). Set
  `AGENT_BACKEND_URL` in the web deployment.

## Patterns

- Keep the web client calling `/api/*`; hide backend placement behind Next rewrites.
- Keep token generation and the App Certificate in `server/`.
- Keep `instruction_config.py` free of `agora_agent` imports — it must stay unit-testable.
- Use `UpdateAgentsRequestProperties` + `UpdateAgentsRequestPropertiesLlm` for live
  system-prompt updates.

## Anti-patterns

- Do not reintroduce a `llm/` service or Next Route Handlers for agent/token logic.
- Do not put `PORT` in `server/.env.example` (it would clobber the random port
  that `verify:local:fastapi` injects via `load_dotenv(override=True)`).
- Do not link to `docs/ai/` — that progressive-disclosure tree is not present yet.
- Do not reference the upstream example framework by name.

## Commands

```bash
bun run setup
bun run dev
bun run doctor
bun run doctor:local
bun run verify         # web-only, no creds
bun run verify:local   # full local gate
```

Narrower checks: `bun run verify:backend`, `bun run verify:local:fastapi`,
`bun run verify:web:proxy`.

## Done criteria

1. Run the narrowest relevant verification command.
2. Web-affecting changes: `bun run verify:web` passes.
3. Backend-affecting changes: `bun run verify:local` (or the narrower
   `verify:local:fastapi` / `verify:backend`) passes.
4. If you change required env vars or setup steps, update the root README,
   ARCHITECTURE.md, and `server/.env.example` together.

## Git conventions

- Conventional Commits: `type: description` or `type(scope): description`
  (`feat`, `fix`, `chore`, `test`, `docs`). Lowercase after the prefix, present
  tense.
- No AI tool names in commit messages or PR descriptions. No `Co-Authored-By`
  trailers. No `--no-verify`. No git config changes.
- Branch names: `type/short-description` (e.g. `feat/update-instructions`).
