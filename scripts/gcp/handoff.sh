#!/usr/bin/env bash
# Finish the GCP extraction burst: stop containers, rsync the populated
# docintel.sqlite (+ RAG chunks) back to the Synology, and print the
# commands to restart Synology's workers and destroy the VM.
#
# Usage:
#   bash scripts/gcp/handoff.sh <synology-tailscale-ip>
#
# Run this when extraction is either fully done (pending=0) OR when you
# want to cut the run short and keep whatever was extracted so far.

set -euo pipefail

log()  { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m!! %s\033[0m\n' "$*"; exit 1; }

if [[ $# -lt 1 ]]; then
  die "Usage: $0 <synology-tailscale-ip>"
fi

SYN_IP="$1"
SYN_USER="${SYN_USER:-Payal}"
REPO_DIR="$HOME/company-brain"

cd "$REPO_DIR"

log "Pre-handoff progress snapshot"
sudo docker exec company-brain-worker python -c "
from app import docintel, rag
d = docintel.stats(); r = rag.stats()
print(f'Extracted  : {d.get(\"files_extracted\", 0):,}')
print(f'Pending    : {d.get(\"pdfs_pending\", 0):,}')
print(f'Entities   : {d.get(\"entities_indexed\", 0):,}')
print(f'RAG indexed: {r.get(\"files_indexed\", 0):,} ({r.get(\"chunks\", 0):,} chunks)')
" 2>/dev/null || true

echo
read -r -p "Proceed with handoff? This will stop the GCP containers. [yes/no]: " confirm
if [[ "$confirm" != "yes" ]]; then
  echo "Aborted. Containers still running."
  exit 0
fi

log "Stopping GCP containers gracefully (so WAL is flushed)"
sudo docker compose -f docker-compose.gcp.yml stop
sleep 3
# The SIGTERM-TIMEOUT dance closes SQLite connections cleanly; after this
# the -shm / -wal files should be merged back into docintel.sqlite.

log "Verifying DB is consistent"
sudo docker run --rm -v "$REPO_DIR/data:/data" python:3.12-slim \
  python -c "
import sqlite3
c = sqlite3.connect('/data/docintel.sqlite')
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
c.close()
print('  WAL checkpoint complete — DB is consistent.')
" 2>/dev/null

log "Rsyncing data back to Synology at $SYN_IP"
# IMPORTANT: This writes to a STAGING dir on the Synology first. The user
# will move it into place once they verify. We do not clobber Synology's
# ./data/ automatically — too risky if something went wrong.
rsync -av --progress --partial --inplace \
  -e "ssh -o StrictHostKeyChecking=accept-new" \
  "$REPO_DIR/data/docintel.sqlite" \
  "$REPO_DIR/data/docintel.sqlite-shm" \
  "$REPO_DIR/data/docintel.sqlite-wal" \
  "$REPO_DIR/data/nas-index.sqlite" \
  "$REPO_DIR/data/hf/" \
  "$SYN_USER@$SYN_IP:/tmp/company-brain-data-incoming/" \
  2>&1 | tail -20 || die "rsync failed. Check SSH connectivity."

log "Handoff data staged on Synology at /tmp/company-brain-data-incoming/"
echo
echo -e "\033[1;32mNow do these two things:\033[0m"
echo
echo "1. On the SYNOLOGY SSH session, move staged files into place:"
echo
echo "     sudo mv /tmp/company-brain-data-incoming/docintel.sqlite \\"
echo "             /volume1/docker/company-brain/data/docintel.sqlite"
echo "     sudo rm -f /volume1/docker/company-brain/data/docintel.sqlite-shm \\"
echo "                /volume1/docker/company-brain/data/docintel.sqlite-wal"
echo "     sudo mv /tmp/company-brain-data-incoming/nas-index.sqlite \\"
echo "             /volume1/docker/company-brain/data/nas-index.sqlite"
echo "     sudo rm -rf /tmp/company-brain-data-incoming"
echo
echo "2. On the SYNOLOGY, restart the workers:"
echo
echo "     sudo docker start company-brain-worker company-brain-rag"
echo
echo "3. On your local machine or GCP Cloud Shell, DESTROY this VM to stop billing:"
echo
echo "     gcloud compute instances delete company-brain-worker \\"
echo "       --project=company-brain-494118 \\"
echo "       --zone=us-west1-b \\"
echo "       --quiet"
echo
echo -e "\033[1;33mBilling keeps running until the VM is deleted.\033[0m"
