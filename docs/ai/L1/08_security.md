# 08 · Security

> Trust boundaries, secret handling, and auth for the instructions recipe.

## Trust boundaries

| Hop                          | Auth                                                                 |
| ---------------------------- | -------------------------------------------------------------------- |
| Browser → agent backend      | None in local dev (the `/api/*` rewrite is same-origin).             |
| Agent backend → Agora cloud  | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.   |
| Agora cloud → OpenAI         | Agora-managed (keyless) by default; BYO `OPENAI_API_KEY` forwarded if set. |

## Secret handling

- **Server-only secrets:** `AGORA_APP_CERTIFICATE` lives only in `server/.env.local` and never reaches the browser. The browser receives a short-lived token, never the certificate.
- `OPENAI_API_KEY` is optional. If set, it lives in `server/.env.local` only and is passed to the `OpenAI(...)` vendor constructor; it never reaches the browser.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholders and comments only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- `Agent.update_instructions()` rejects empty `agent_id` or `instructions`, and raises `ValueError` for unknown `agent_id` (no active session).
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; SDK exceptions map to 400/500 without leaking internals to the client beyond the message.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- The published Docker image is **backend-only** (`:8000`); it does not bundle secrets.
- `OPENAI_API_KEY` if set must be provided via the container's env, not embedded in the image.

## Related Deep Dives

- None.
