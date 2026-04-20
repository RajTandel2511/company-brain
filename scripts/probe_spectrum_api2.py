"""Discover Spectrum's actual API path structure."""
import base64, json, sys, urllib.parse as up
from pathlib import Path
import requests

BASE = "https://allairmechanical.dexterchaney.com:8482"
CLIENT_ID = "Spectrum-EB9A4694F"
CLIENT_SECRET = "4E070A9D-9C7C-4248-AC43-6698FE7C7CC2"

# Token
r = requests.post(
    BASE + "/connect/token",
    data={"grant_type": "client_credentials", "client_id": CLIENT_ID,
          "client_secret": CLIENT_SECRET, "scope": "spectrumapi"},
    timeout=15,
)
token = r.json()["access_token"]
print(f"Token OK ({token[:20]}…)")
H = {"Authorization": f"Bearer {token}"}


def probe(path):
    r = requests.get(BASE + path, headers=H, timeout=20, allow_redirects=False)
    body = r.text[:200]
    print(f"  {r.status_code}  {path:<60}  {body!r}")
    return r


# Discovery endpoints
print("\n=== Discovery ===")
for path in [
    "/", "/api", "/spectrum", "/spectrum/api",
    "/.well-known/openid-configuration",
    "/.well-known/openid_configuration",
    "/.well-known/oauth-authorization-server",
    "/connect", "/connect/authorize",
    "/sdx", "/sdx/api", "/SDX", "/SDX/API",
    "/help", "/Help",
    "/swagger/docs", "/swagger/docs/v1",
    "/webservices", "/WebServices",
    "/ws",
    "/services",
    "/api/swagger/docs/v1",
]:
    probe(path)

# Common Spectrum web service names
print("\n=== Web service modules (various prefixes) ===")
for prefix in ["", "/api", "/spectrum", "/spectrum/api", "/sdx", "/sdx/api", "/webservices", "/ws", "/services", "/SpectrumAPI", "/spectrumapi"]:
    for mod in ["AP", "JC", "GL", "AR"]:
        probe(f"{prefix}/{mod}")
