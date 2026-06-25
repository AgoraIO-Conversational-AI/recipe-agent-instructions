---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: agent.instructions
    name: System prompt, template variables, reply style, and exit message
  - id: agent.live-update
    name: Runtime system-prompt swap via POST /updateInstructions
  - id: api.routes
    name: Browser-facing API routes
  - id: web.conversation-ui
    name: Conversation UI panels and controls
  - id: verification.contracts
    name: Contract, proxy, and local FastAPI smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate stays in the Python backend. OPENAI_API_KEY, if set, stays server-only.
  - id: llm.agora-managed
    summary: The OpenAI LLM is Agora-managed (keyless) by default; OPENAI_API_KEY is optional for BYO-key accounts.
  - id: instruction_config.purity
    summary: instruction_config.py has no agora_agent imports; it is a pure module for unit-testable builders.
  - id: template_variables.vendor-resolved
    summary: "{{assistant_name}} and {{today}} placeholders are resolved by the Agora vendor, not by Python code."
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID and AGORA_APP_CERTIFICATE are required; AGENT_BACKEND_URL is required by deployed web rewrites.
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, and POST /api/stopAgent remain the browser-facing contract.
  - id: api.update-route
    summary: POST /updateInstructions (backend-direct, not rewritten) swaps the live system prompt.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **instructions** quickstart: a managed OpenAI cascade (Deepgram STT + keyless OpenAI LLM + MiniMax TTS) behind a Next.js web client, with configurable system prompts and live runtime updates.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers building a configurable voice agent whose personality and behavior are driven entirely by system-prompt features — without a separate LLM service.
- Reuse model: clone, bind project, run, then customize prompts, template variables, or reply style.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- A cascading Deepgram STT → Agora-managed (keyless) OpenAI LLM → MiniMax TTS pipeline via `with_stt/with_llm/with_tts`.
- Pure instruction builders in `instruction_config.py` (no SDK dependency, fully unit-testable).
- Live system-prompt swap via `POST /updateInstructions` + `session.update(...)` without session restart.
- Next.js browser UI with RTC audio, RTM transcript/metrics, connection status.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, and local FastAPI smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI integration from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `agent.instructions` | `server/src/instruction_config.py`, `server/src/agent.py` | Edit `build_instructions()`, `build_template_variables()`, `reply_max_tokens()`, or `OPENAI_MODEL`/`REPLY_STYLE`/`ASSISTANT_NAME`/`AGENT_EXIT_MESSAGE` env. | Run `cd server && pytest tests -v`; document new env in `server/.env.example` (never add `PORT`). |
| `agent.live-update` | `server/src/agent.py`, `server/src/server.py`, `server/src/instruction_config.py` | Extend `update_instructions()` or add new update payloads using `UpdateAgentsRequestProperties`. | Ensure the session is in `_sessions`; add test coverage in `test_instruction_config.py`. |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call, transcript, metrics, connection status, mic, or visualizer UI. | Preserve RTC/RTM lifecycle ownership and transcript UID normalization. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, and `/api/stopAgent` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, and agent lifecycle.
- `instruction_config.py` has no `agora_agent` import — keep it pure.
- `{{assistant_name}}` and `{{today}}` are vendor-resolved, not pre-substituted in Python.
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` |
| Optional backend env | `OPENAI_API_KEY`, `OPENAI_MODEL`, `REPLY_STYLE`, `ASSISTANT_NAME`, `AGENT_EXIT_MESSAGE`, `AGENT_GREETING`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, parameters? }`; returns `data.agent_id`, `data.channel_name`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| `POST /updateInstructions` | Body `{ agentId, instructions }`; returns `{ code: 0, msg: "success" }`. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact model name, voice ID, STT language, and greeting text, as long as they stay documented extension points.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, and commands.
- `L1/02_architecture.md` — request flow and topology.
- `L1/05_workflows.md` — common modification workflows.
- `L1/06_interfaces.md` — route, rewrite, env, and vendor contracts.
- `L1/L2/instruction_config_and_update.md` — full instruction builder and live update detail.
- `L1/L2/session_lifecycle.md` — RTC/RTM/session orchestration.
