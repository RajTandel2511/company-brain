#!/usr/bin/env bash
# Quick health + progress check for the GCP extraction run.
#
# Usage:
#   bash scripts/gcp/monitor.sh
#
# Can be run ad-hoc or in a loop:
#   watch -n 60 'bash ~/company-brain/scripts/gcp/monitor.sh'

set -euo pipefail

cd "$HOME/company-brain"

echo '=== CONTAINERS ==='
sudo docker compose -f docker-compose.gcp.yml ps 2>/dev/null | \
  awk 'NR==1 || /company-brain/'

echo
echo '=== MEMORY / CPU ==='
sudo docker stats --no-stream --format \
  'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' \
  company-brain-worker company-brain-rag 2>/dev/null

echo
echo '=== PROGRESS ==='
sudo docker exec company-brain-worker python -c "
from app import docintel, rag
d = docintel.stats(); r = rag.stats()
total = d.get('files_extracted', 0) + d.get('pdfs_pending', 0)
ext = d.get('files_extracted', 0)
pct = (ext / total * 100) if total else 0
print(f'Extracted  : {ext:,} / {total:,} ({pct:.2f}%)')
print(f'Entities   : {d.get(\"entities_indexed\", 0):,}')
print(f'RAG indexed: {r.get(\"files_indexed\", 0):,} ({r.get(\"chunks\", 0):,} chunks)')
" 2>/dev/null

echo
echo '=== WORKER (last 10 lines) ==='
sudo docker logs --tail 10 company-brain-worker 2>&1 | sed 's/^/  /'

echo
echo '=== RAG (last 5 lines) ==='
sudo docker logs --tail 5 company-brain-rag 2>&1 | sed 's/^/  /'

echo
echo '=== DISK ==='
df -h / | awk 'NR==1 || /\/$/'
du -sh ~/company-brain/data/ 2>/dev/null | sed 's|^|  data dir: |'

echo
echo '=== ERRORS (last 200 lines, filtered) ==='
for c in company-brain-worker company-brain-rag; do
  err=$(sudo docker logs --tail 200 "$c" 2>&1 | \
        grep -iE 'traceback|exception|killed|oom' | \
        grep -v 'write lock busy' | tail -3)
  if [[ -n "$err" ]]; then
    echo "--- $c ---"
    echo "$err" | sed 's/^/  /'
  fi
done
echo 'done.'
