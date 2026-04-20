# Company Brain

An AI-powered operations layer for a construction company running on **Trimble Spectrum by Viewpoint** + **Synology NAS**.

- Natural-language chat over Spectrum data ("which jobs are over budget?", "show me all RFIs on Marriott")
- Live KPI dashboard — jobs, WIP, cost variance, cash flow
- Document search across the NAS (drawings, PDFs, photos) linked to Spectrum records
- Proactive alerts when jobs trend sideways

**Read-only** against Spectrum. Runs entirely in-house on Synology Docker. Data never leaves your LAN.

## Stack
- Backend: FastAPI (Python) + pyodbc → MSSQL (Spectrum)
- AI: Claude Haiku 4.5 by default (cheap) — swappable to local Ollama for $0
- Frontend: React + Vite + Tailwind
- Deploy: Docker Compose on Synology DSM (Container Manager)

## Cost controls (built in)
- Default model is **Claude Haiku 4.5** — ~15× cheaper than Opus.
- **Prompt caching** on the schema block gives ~90% off on cache reads.
- **Response cache** (SQLite) returns identical questions for free for `RESPONSE_CACHE_TTL` seconds.
- Flip `LLM_PROVIDER=ollama` in `.env` to run a local model (Qwen2.5-Coder, Llama 3.x) for zero API spend.
- Set `ANTHROPIC_SUMMARY_MODEL=claude-sonnet-4-6` if you want Haiku for SQL gen and Sonnet only for the final writeup.

## Quick start
1. Copy `.env.example` → `.env` and fill in Spectrum SQL + Anthropic API creds.
2. On Synology: Container Manager → Project → Upload this folder → `docker compose up -d`.
3. Open `http://<synology-ip>:8080` in your browser.

See `docs/DEPLOY.md` for full Synology setup.
