#!/usr/bin/env bash
# Seed the extraction DB from Synology and kick off the GCP extraction burst.
#
# Usage:
#   bash scripts/gcp/start.sh <synology-tailscale-ip>
#
# Prerequisites (done by bootstrap.sh + mount_nas.sh):
#   - docker + compose installed
#   - Tailscale up, Synology reachable
#   - /mnt/nas/* mounted via SMB
#
# This script ASSUMES:
#   - You've stopped the Synology worker + rag_worker already. If you
#     haven't, it prompts you to confirm before pulling the DB.
#   - The Synology has SSH enabled and the user can connect via Tailscale.

set -euo pipefail

log()  { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m!! %s\033[0m\n' "$*"; exit 1; }

if [[ $# -lt 1 ]]; then
  die "Usage: $0 <synology-tailscale-ip>    (same IP you used for mount_nas.sh)"
fi

SYN_IP="$1"
SYN_USER="${SYN_USER:-Payal}"   # override with SYN_USER=... if your SSH user differs
REPO_DIR="$HOME/company-brain"

cd "$REPO_DIR"

log "Sanity check — NAS mounts"
REQUIRED_SHARES=(Accounting Current_Bids Estimation Projects Common_Submittals)
for s in "${REQUIRED_SHARES[@]}"; do
  if ! mountpoint -q "/mnt/nas/$s"; then
    warn "/mnt/nas/$s is not mounted."
    die "Run scripts/gcp/mount_nas.sh first."
  fi
done
echo "  all critical NAS mounts look good"

log "Sanity check — .env file"
if [[ ! -f .env ]]; then
  warn ".env missing. Create it now from .env.example (same values as Synology)."
  die "Aborting — .env is required for Spectrum DB credentials."
fi
echo "  .env present"

log "Confirming Synology workers are stopped"
echo "  Before we pull data from Synology, the Synology workers MUST be stopped."
echo "  Run this on the Synology SSH session (in another terminal):"
echo "    sudo docker stop company-brain-worker company-brain-rag"
echo
read -r -p "  Have you stopped them? [yes/no]: " confirm
if [[ "$confirm" != "yes" ]]; then
  die "Abort — go stop them, then re-run this script."
fi

log "Pulling seed data from Synology ($SYN_IP) via rsync over Tailscale"
# --inplace keeps disk usage sane for big SQLite files; --partial survives drops
# Using -avz (archive+verbose+compress). Could skip -z if LAN-like speeds.
mkdir -p data
rsync -av --progress --partial --inplace \
  -e "ssh -o StrictHostKeyChecking=accept-new" \
  "$SYN_USER@$SYN_IP:/volume1/docker/company-brain/data/" \
  "$REPO_DIR/data/" \
  || die "rsync failed. Check SSH connectivity to the Synology."

# Clean up WAL artifacts — the Synology containers were stopped so the DB
# should be consistent, but the -shm / -wal files can linger and confuse us.
rm -f data/docintel.sqlite-shm data/docintel.sqlite-wal 2>/dev/null || true

log "Seed data state"
ls -lh data/*.sqlite 2>/dev/null
echo
sudo docker run --rm -v "$REPO_DIR/data:/data" python:3.12-slim \
  python -c "
import sqlite3, os
db = '/data/docintel.sqlite'
if os.path.exists(db):
    c = sqlite3.connect(db)
    try:
        fe = c.execute('SELECT COUNT(*) FROM file_content').fetchone()[0]
        ch = c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='chunks'\").fetchone()[0]
        chs = c.execute('SELECT COUNT(*) FROM chunks').fetchone()[0] if ch else 0
        print(f'  files_extracted (file_content rows): {fe:,}')
        print(f'  rag chunks: {chs:,}')
    except Exception as e:
        print(f'  (error reading DB: {e})')
    c.close()
else:
    print('  docintel.sqlite NOT present — fresh start')
" 2>/dev/null || true

log "Building GCP image (first run takes ~3-5 minutes)"
sudo docker compose -f docker-compose.gcp.yml build

log "Starting worker + rag_worker"
sudo docker compose -f docker-compose.gcp.yml up -d

sleep 5

log "Container status"
sudo docker compose -f docker-compose.gcp.yml ps

echo
echo -e "\033[1;32mExtraction is live on GCP.\033[0m"
echo
echo "Useful commands:"
echo "  Watch worker:      sudo docker logs -f company-brain-worker"
echo "  Watch RAG:         sudo docker logs -f company-brain-rag"
echo "  Progress check:    bash scripts/gcp/monitor.sh"
echo "  Stop everything:   sudo docker compose -f docker-compose.gcp.yml down"
echo
echo "When extraction is done (pending=0), run:"
echo "  bash scripts/gcp/handoff.sh $SYN_IP"
