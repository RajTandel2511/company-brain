#!/usr/bin/env bash
# One-time VM bootstrap. Run ONCE on a fresh Ubuntu 22.04 GCP VM.
#
#   curl -fsSL https://raw.githubusercontent.com/RajTandel2511/company-brain/main/scripts/gcp/bootstrap.sh | bash
#
# Or: git clone, then bash scripts/gcp/bootstrap.sh
#
# When it finishes, you'll need to:
#   1. Log out and back in (for docker group membership)
#   2. Run `sudo tailscale up` and authenticate in the browser
#   3. Run scripts/gcp/mount_nas.sh <synology-tailscale-ip>

set -euo pipefail

log()  { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*"; }

if [[ "$(id -u)" == "0" ]]; then
  warn "Do not run this script as root. Run as the default ubuntu user — it'll sudo as needed."
  exit 1
fi

log "Updating package lists"
sudo apt-get update -qq

log "Installing prerequisites (git, cifs-utils, rsync, curl, jq)"
sudo apt-get install -y -qq \
  git cifs-utils rsync curl jq ca-certificates gnupg

log "Installing Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
else
  echo "  docker already installed, skipping"
fi

log "Verifying docker compose plugin"
sudo docker compose version || { warn "Docker Compose plugin missing"; exit 1; }

log "Installing Tailscale"
if ! command -v tailscale >/dev/null 2>&1; then
  curl -fsSL https://tailscale.com/install.sh | sh
else
  echo "  tailscale already installed, skipping"
fi

log "Cloning company-brain repo"
cd ~
if [[ ! -d company-brain ]]; then
  git clone https://github.com/RajTandel2511/company-brain.git
else
  echo "  ~/company-brain already exists, pulling latest"
  cd company-brain && git pull && cd ~
fi

log "Creating mount points for NAS shares"
for share in Accounting AI_RAG_Data All_Air_Users Common_Submittals \
             Current_Bids Employee_Resources Estimation Foremen_Portal \
             Forms Inventory Miscallaneous Office_Use_Only Projects \
             Service_Tech_Portal Service_Dept Trial-1; do
  sudo mkdir -p "/mnt/nas/$share"
done

cat <<EOF


\033[1;32mBootstrap complete.\033[0m

Next steps — in this order:

  1. Log out and back in (so docker group membership takes effect):
       exit
       # then ssh back in via GCP console

  2. Connect this VM to your Tailscale network:
       sudo tailscale up
     Copy the URL it prints, open it in a browser, authenticate, and approve
     this machine on the Tailscale admin page.

  3. Get this VM's Tailscale IP — you'll need it later:
       tailscale ip -4

  4. Mount the Synology's NAS shares (needs the Synology's Tailscale IP):
       cd ~/company-brain
       bash scripts/gcp/mount_nas.sh <synology-tailscale-ip>

  5. Seed data from Synology + start extraction:
       bash scripts/gcp/start.sh <synology-tailscale-ip>

EOF
