# 07 · Gotchas

> Non-obvious pitfalls specific to the instructions recipe. Read before changing the agent, env, instruction builders, or verify scripts.

## `OPENAI_API_KEY` is optional, not required

This recipe uses Agora's **managed OpenAI vendor** (keyless). `OPENAI_API_KEY` is passed to the `OpenAI(...)` vendor constructor only if set; Agora provides its own key otherwise. Do not make it required or add a boot-time check for it — the server and sessions start fine without it.

## Keep `instruction_config.py` free of SDK imports

`server/src/instruction_config.py` must not import from `agora_agent`. Its entire value is that it is a pure Python module, unit-testable without the SDK. If you need to add a new builder, keep it a plain function returning strings, dicts, or lists.

## Template variables are resolved by the vendor, not by Python code

`{{assistant_name}}` and `{{today}}` appear literally in the string returned by `build_instructions()`. They are substituted by the Agora managed vendor at session start using `template_variables={"assistant_name": ..., "today": ...}`. Do not call `.replace("{{assistant_name}}", ...)` yourself — that would bypass the vendor substitution and break the feature.

## `REPLY_STYLE=short` changes both `max_tokens` and the prompt

Setting `REPLY_STYLE=short` lowers `max_tokens` to 40 **and** injects "Always answer in one short sentence." into the system prompt via `build_instructions`. The two are intentionally coupled — if you change one, check the other.

## `POST /updateInstructions` requires an active session

`update_instructions(agent_id, instructions)` raises `ValueError` if `agent_id` is not in `self._sessions`. Unlike `stop()`, it does **not** fall back to the stateless cloud path. The session must be in the current process's memory map. If the backend was restarted, the old `agent_id` will not be found.

## `POST /updateInstructions` is not in the Next rewrite map

Only `get_config`, `startAgent`, and `stopAgent` are rewritten. `updateInstructions` is not in `web/next.config.ts` and is not called by the web client. It is intended for server-side or scripted use (e.g. via `curl` to the backend directly).

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` and loads env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic belongs in `server/`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid`; `UpdateInstructionsRequest` uses `agentId`, `instructions` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `socksio` (in `requirements.txt`) plus `all_proxy` to route through SOCKS.

## Related Deep Dives

- [instruction_config_and_update.md](L2/instruction_config_and_update.md) — correct instruction builder and live update wiring.
