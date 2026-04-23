#!/usr/bin/env bash
# Mount Synology NAS shares over SMB via Tailscale.
#
# Usage:
#   bash scripts/gcp/mount_nas.sh <synology-tailscale-ip>
#
# First run prompts for the Synology SMB username/password and writes them
# to /etc/cifs-credentials (root-only, 0600). Subsequent runs reuse it.
#
# Mounts are added to /etc/fstab so they persist across reboots.

set -euo pipefail

log()  { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m!! %s\033[0m\n' "$*"; exit 1; }

if [[ $# -lt 1 ]]; then
  die "Usage: $0 <synology-tailscale-ip>    (e.g. 100.64.5.42)"
fi

SYN_IP="$1"
CREDS_FILE="/etc/cifs-credentials"

# Validate IP shape (just basic sanity, not strict)
if ! [[ "$SYN_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  die "Doesn't look like an IP: $SYN_IP"
fi

log "Testing Tailscale connectivity to Synology at $SYN_IP"
if ! ping -c 2 -W 3 "$SYN_IP" >/dev/null 2>&1; then
  warn "Can't ping $SYN_IP — is Tailscale up on both machines?"
  warn "Check 'tailscale status' on both the VM and the Synology."
  die "Aborting."
fi
echo "  Synology reachable over Tailscale"

# Prompt for credentials if not already saved
if ! sudo test -f "$CREDS_FILE"; then
  log "First run — need Synology SMB credentials"
  echo "  These get written to $CREDS_FILE (root-only, 0600) and reused."
  read -r -p "  Synology SMB username (usually Payal): " SMB_USER
  read -r -s -p "  Synology SMB password: " SMB_PASS; echo

  sudo bash -c "cat > $CREDS_FILE" <<EOF
username=$SMB_USER
password=$SMB_PASS
EOF
  sudo chmod 600 "$CREDS_FILE"
  sudo chown root:root "$CREDS_FILE"
  echo "  Credentials saved."
else
  echo "  Using existing credentials at $CREDS_FILE"
fi

# Share names on Synology → mount point name on the VM.
# Left side must match the actual share name on DSM (with spaces where DSM
# has them). Right side must match the paths in docker-compose.gcp.yml.
declare -A SHARES=(
  ["Accounting"]="Accounting"
  ["AI_RAG_Data"]="AI_RAG_Data"
  ["All_Air_Users"]="All_Air_Users"
  ["Common_Submittals"]="Common_Submittals"
  ["Current_Bids"]="Current_Bids"
  ["Employee Resources"]="Employee_Resources"
  ["Estimation"]="Estimation"
  ["Foremen Portal"]="Foremen_Portal"
  ["Forms"]="Forms"
  ["Inventory"]="Inventory"
  ["Miscallaneous"]="Miscallaneous"
  ["Office_Use_Only"]="Office_Use_Only"
  ["Projects"]="Projects"
  ["Service Tech Portal"]="Service_Tech_Portal"
  ["Service_Dept"]="Service_Dept"
  ["Trial-1"]="Trial-1"
)

log "Writing fstab entries + mounting shares"
# Back up fstab once
if [[ ! -f /etc/fstab.backup-company-brain ]]; then
  sudo cp /etc/fstab /etc/fstab.backup-company-brain
  echo "  Backed up /etc/fstab to /etc/fstab.backup-company-brain"
fi

# Strip any previous company-brain fstab lines so re-running is idempotent.
sudo sed -i '/# company-brain mount/d' /etc/fstab
sudo sed -i "\|//$SYN_IP/.*cifs|d" /etc/fstab

FAILED=()
for share in "${!SHARES[@]}"; do
  mount_dir="${SHARES[$share]}"
  mount_point="/mnt/nas/$mount_dir"
  sudo mkdir -p "$mount_point"

  # URL-encode spaces in share name (cifs wants them escaped)
  share_escaped="${share// /\\040}"

  # fstab line: ro mount, soft timeout so a dead share doesn't hang the box
  line="//$SYN_IP/$share_escaped  $mount_point  cifs  credentials=$CREDS_FILE,ro,iocharset=utf8,uid=0,gid=0,file_mode=0444,dir_mode=0555,soft,noperm,vers=3.0,_netdev  0  0  # company-brain mount"
  echo "$line" | sudo tee -a /etc/fstab >/dev/null

  # Unmount if a stale mount is there, then mount fresh
  if mountpoint -q "$mount_point"; then
    sudo umount "$mount_point" 2>/dev/null || true
  fi

  if sudo mount "$mount_point" 2>/tmp/mount.err; then
    count=$(ls "$mount_point" 2>/dev/null | wc -l)
    echo "  ✓ mounted $share -> $mount_point ($count items visible)"
  else
    FAILED+=("$share: $(cat /tmp/mount.err 2>/dev/null | head -1)")
  fi
done

if [[ ${#FAILED[@]} -gt 0 ]]; then
  warn "Some shares failed to mount:"
  for f in "${FAILED[@]}"; do echo "    - $f"; done
  warn "Check the share names match what's on DSM (Control Panel → Shared Folder)."
  warn "You can re-run this script after fixing the names in the SHARES map above."
fi

log "Mount summary"
df -h -t cifs 2>/dev/null | head -n 25 || true

echo
echo -e "\033[1;32mNAS mounts ready.\033[0m"
echo "Next: bash scripts/gcp/start.sh $SYN_IP"
