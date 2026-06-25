# recipe-agent-instructions — Repo Card

> Next.js web client + Python FastAPI backend for an Agora Conversational AI voice agent driven by Agora's managed OpenAI cascade (Deepgram STT + keyless OpenAI LLM + MiniMax TTS). Demonstrates system-prompt customization, template variables, reply-style control, and live runtime instruction updates.

## Identity

| Field          | Value                                                                       |
| -------------- | --------------------------------------------------------------------------- |
| Repo           | `AgoraIO-Conversational-AI/recipe-agent-instructions`                       |
| Type           | `distributed-system` (single repo, two co-located processes)                |
| Language       | Python 3.10+ (FastAPI + uvicorn) backend + Next.js 16 / React 19 web        |
| Deploy Target  | `web/` as Next.js app, `server/` as a reachable FastAPI service             |
| Owner          | Agora Conversational AI DevEx                                               |
| Last Reviewed  | 2026-06-25                                                                  |
| Recipe Role    | `base`                                                                      |
| Recipe Version | `1.0.0`                                                                     |
| Recipe Status  | `experimental`                                                              |

## L1 — Summaries

The Audience column helps agents prioritise: **Use** = consuming the recipe's behavior, **Maintain** = modifying internals.

| File                                     | Purpose                                                                               | Audience       |
| ---------------------------------------- | ------------------------------------------------------------------------------------- | -------------- |
| [01_setup](L1/01_setup.md)               | bun + venv + pip setup, env vars (zero-key: `OPENAI_API_KEY` optional), commands     | Use & Maintain |
| [02_architecture](L1/02_architecture.md) | Two-process topology, `/api/*` rewrite proxy, cascading STT/LLM/TTS lifecycle        | Maintain       |
| [03_code_map](L1/03_code_map.md)         | `web/` and `server/` trees with key file responsibilities                             | Maintain       |
| [04_conventions](L1/04_conventions.md)   | Python async + FastAPI patterns, Biome, JSON envelope, instruction builders           | Maintain       |
| [05_workflows](L1/05_workflows.md)       | Change system prompt, add a route, live update, adjust reply style, verify, deploy    | Use            |
| [06_interfaces](L1/06_interfaces.md)     | FastAPI route contracts, rewrites, env vars, `OpenAI` vendor config                   | Use & Maintain |
| [07_gotchas](L1/07_gotchas.md)           | Zero-key nuance, `instruction_config.py` purity, `PORT` in env, VAD placement        | Maintain       |
| [08_security](L1/08_security.md)         | Token007, App Certificate server-only, CORS, keyless vs BYO-key                      | Maintain       |

## Recipe Profile

This repo declares `Recipe Role: base`. See [RECIPE.md](RECIPE.md) for extension points, invariants, and stable contracts before changing reusable surfaces.
