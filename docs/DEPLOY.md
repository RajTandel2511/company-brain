# Deploying Company Brain on Synology

## 1. Prep
- DSM 7.2+ with **Container Manager** installed (Package Center → Container Manager).
- The NAS share you want to expose — e.g. `/volume1/projects`. Read-only mount is enforced in `docker-compose.yml`.
- Spectrum SQL Server reachable from the Synology (open port 1433 or put both on the same VLAN).
- An Anthropic API key (https://console.anthropic.com/).

## 2. Upload the project
1. SSH into the NAS or use File Station to copy this folder to `/volume1/docker/company-brain`.
2. `cp .env.example .env` and fill in:
   - `SPECTRUM_SQL_HOST`, `SPECTRUM_SQL_USER`, `SPECTRUM_SQL_PASSWORD`
   - `ANTHROPIC_API_KEY`
3. Edit `docker-compose.yml` — change the NAS mount line to your actual share:
   ```yaml
   - /volume1/projects:/mnt/nas:ro
   ```

## 3. Launch
**Option A — Container Manager UI**
- Container Manager → Project → Create → point at `/volume1/docker/company-brain` → Next → Build.

**Option B — SSH**
```bash
cd /volume1/docker/company-brain
sudo docker compose up -d --build
sudo docker compose logs -f
```

## 4. Open it
`http://<synology-ip>:8080`

## 5. Tighten
- Put it behind Synology's reverse proxy + Let's Encrypt if exposed outside LAN.
- Add Synology firewall rules to limit access to trusted subnets.
- Rotate the Anthropic key quarterly.

## Troubleshooting
- **Backend can't reach SQL**: confirm `SPECTRUM_SQL_HOST` is an IP or FQDN the Synology can resolve. Test with `docker exec -it company-brain-backend bash` then `apt-get install -y iputils-ping && ping <host>`.
- **Dashboard panels 500**: the default SQL targets `dbo.JobMaster` / `dbo.ARInvoiceAging`. Spectrum's schema varies by version — edit `DASHBOARD_QUERIES` in `backend/app/main.py` to match your install.
- **AI says "unsafe SQL"**: by design — only single-statement `SELECT`/`WITH` runs. Re-ask the question more specifically.
