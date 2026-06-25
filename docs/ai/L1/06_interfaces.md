# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the managed `OpenAI` vendor config.

## Backend routes (port 8000)

The browser calls these as `/api/<name>`; Next rewrites to the backend `/<name>`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, parameters?: object }`.
  - `parameters.output_audio_codec?: string` is the only honored parameter field.
- Returns `data`: `{ agent_id, channel_name, status: "started" }`.
- 400 if `channelName`/`rtcUid`/`userUid` invalid.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

### `POST /updateInstructions`

- Body: `{ agentId: string, instructions: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).
- 400 if `agentId` or `instructions` empty, or no active session for the given `agentId`.
- Swaps the running session's system prompt via `session.update(UpdateAgentsRequestProperties(...))`. Session stays running.

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path               | Backend destination    |
| -------------------------- | ---------------------- |
| `/api/get_config`          | `/get_config`          |
| `/api/startAgent`          | `/startAgent`          |
| `/api/stopAgent`           | `/stopAgent`           |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`. Note: `/updateInstructions` is **not** in the rewrite map; it is intended for server-side or backend-to-backend use.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `startAgent(channelName, rtcUid, userUid) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope          | Required | Default                              |
| ----------------------- | -------------- | :------: | ------------------------------------ |
| `AGORA_APP_ID`          | backend        |    ✅    | —                                    |
| `AGORA_APP_CERTIFICATE` | backend        |    ✅    | —                                    |
| `OPENAI_API_KEY`        | backend        |          | — (optional; Agora-managed keyless)  |
| `OPENAI_MODEL`          | backend        |          | `gpt-4o-mini`                        |
| `REPLY_STYLE`           | backend        |          | `normal`                             |
| `ASSISTANT_NAME`        | backend        |          | `Ada`                                |
| `AGENT_EXIT_MESSAGE`    | backend        |          | `Thanks for chatting — goodbye!`     |
| `AGENT_GREETING`        | backend        |          | built-in line                        |
| `AGENT_BACKEND_URL`     | web (deploy)   |   ✅\*   | `http://localhost:8000` (dev)        |
| `PORT`                  | backend (env only) |      | `8000` — do **not** put in `.env.example` |

\* Required wherever the web app is deployed; rewrites are empty without it.

## Managed `OpenAI` vendor config (`agent.py`)

`OpenAI(api_key?, model, system_messages, template_variables, max_tokens, greeting_message, temperature)`:

- `api_key` — optional (Agora-managed by default; set only for BYO-key accounts).
- `model` — `OPENAI_MODEL`, default `gpt-4o-mini`.
- `system_messages` — built by `build_instructions(reply_style, exit_message)`.
- `template_variables` — `{"assistant_name": ..., "today": ...}` from `build_template_variables()`.
- `max_tokens` — `reply_max_tokens(reply_style)` (40 for `short`, 1024 for `normal`).
- `temperature` — `0.7` (fixed).

STT: `DeepgramSTT(model="nova-3", language="en")`. TTS: `MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")`.

## Related Deep Dives

- [instruction_config_and_update.md](L2/instruction_config_and_update.md) — builder internals and live update flow.
