# Synology deployment — step by step

Deploying Company Brain to run **24/7 on the NAS itself**. No laptop dependency,
no SMB latency, worker finishes in 1-2 days.

## What ships

- `backend` container — FastAPI at port **8000**, bind-mounted data dir for SQLite.
- `worker` container — runs `scripts/extract_worker.py` in a loop. Separate container
  so CPU spikes don't make the API unresponsive.
- `frontend` container — nginx serving the built Vite bundle at port **8080**.
- All 24 NAS shares bind-mounted **read-only** under `/mnt/nas/<Share>/`.
- SQLite DBs persisted to `./data/` (host path `/volume1/docker/company-brain/data/`).
- CPU + RAM caps on every container so DSM can't starve.

## Prerequisites

- DSM **7.2+** with **Container Manager** installed (Package Center).
- At least **4 GB RAM free** (the worker uses up to 2 GB during OCR).
- SSH access to the NAS (optional but helpful).
- Outbound internet — the backend talks to Spectrum SQL (`:1433`) and
  `api.anthropic.com:443`.

## 1. Copy the project to the NAS

From your laptop (or via File Station):
```bash
scp -r ./ admin@10.231.0.3:/volume1/docker/company-brain/
```

Then on the NAS:
```bash
cd /volume1/docker/company-brain
cp .env.example .env
vi .env       # fill in SPECTRUM_SQL_*, ANTHROPIC_API_KEY, SPECTRUM_COMPANY_CODE
```

## 2. Do a one-share dry run FIRST

Before unleashing the full worker, run the dry-run against a small share.
This confirms: mounts work, SQL reachable, Tesseract works, doc-intel DB writable.

```bash
sudo docker compose -f docker-compose.synology.yml build
sudo docker compose -f docker-compose.synology.yml run --rm \
  --entrypoint "python scripts/dry_run.py Current_Bids" backend
```

Expected output ends with:
```
If you got here, containers + mounts + SQL + OCR all work.  Ready for full worker.
```

If you see **"FAIL: /mnt/nas/Current_Bids not found"** — the bind mount didn't take.
Check the `volumes:` block in `docker-compose.synology.yml` and make sure your share
names match (DSM is case-sensitive).

## 3. Bring up the real stack

```bash
sudo docker compose -f docker-compose.synology.yml up -d
sudo docker compose -f docker-compose.synology.yml logs -f worker
```

Logs should show the worker picking batches every ~30 seconds.

## 4. Open it

`http://<synology-ip>:8080`

Reverse-proxy through DSM's built-in "Application Portal" if you want HTTPS + a
friendly hostname like `brain.allair.local`. Do **not** expose port 8080 to the
internet without auth.

## 5. Resource tuning

Edit the `deploy.resources.limits` blocks in `docker-compose.synology.yml`:

```yaml
worker:
  deploy:
    resources:
      limits: { cpus: "2.0", memory: 2048M }   # raise if DSM has spare capacity
```

Synology monitor → Resource Monitor → if CPU is routinely at 95% and DSM's own
services feel sluggish, drop the worker to `cpus: "1.0"`.

## 6. Keeping it fresh

The worker runs forever — new files on the NAS are picked up on the next pass.
To pull app updates:
```bash
cd /volume1/docker/company-brain
git pull           # if you put it in git
sudo docker compose -f docker-compose.synology.yml up -d --build
```

## Troubleshooting

**"The network location cannot be reached" or permission denied**
Usually a bind-mount pointing at the wrong DSM path. Check `ls /volume1/` and match
names exactly (spaces and case matter).

**Worker uses 100% CPU and DSM is sluggish**
Lower `cpus` in the worker's `deploy.resources.limits`. Also verify the Synology
model has enough cores (2 cores = set `cpus: "1.0"` max).

**"ODBC Driver 18 for SQL Server not found" on ARM Synology**
Microsoft ships arm64 builds for Debian 12 — our Dockerfile uses the multi-arch
MS repo (`deb [arch=amd64,arm64] …`). If your Synology is a legacy ARMv7 model,
you're out of luck at the ODBC level — those models aren't supported for the
backend. Use a newer model or run the backend elsewhere.

**Worker crashes on one huge PDF**
The extractor already skips broken/oversized PDFs — check worker logs with
`docker compose logs worker --tail 200`. If a specific file keeps crashing, add
its path to a skip list (I'll expose that as an env var on request).
