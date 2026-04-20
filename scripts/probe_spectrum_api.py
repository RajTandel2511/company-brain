"""Get an OAuth token against Spectrum + enumerate the API surface."""
import base64
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE = "https://allairmechanical.dexterchaney.com:8482"
CLIENT_ID = "Spectrum-EB9A4694F"
CLIENT_SECRET = "4E070A9D-9C7C-4248-AC43-6698FE7C7CC2"
SCOPE = "spectrumapi"
AUTH_ID = "Integration"
COMPANY = "AA1"
OPERATOR = "RT1"

TOKEN_URL = BASE + "/connect/token"


def get_token_variants():
    """Try a few common OAuth2 client-credentials variants."""
    results = []
    # 1) Form body
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": SCOPE,
        },
        timeout=15,
    )
    results.append(("form-body", r))

    # 2) Basic auth header, scope+grant_type in body
    basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    r = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {basic}"},
        data={"grant_type": "client_credentials", "scope": SCOPE},
        timeout=15,
    )
    results.append(("basic-auth-header", r))

    # 3) Form body but include Basic header too (some servers pick one)
    r = requests.post(
        TOKEN_URL,
        headers={"Authorization": f"Basic {basic}"},
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": SCOPE,
        },
        timeout=15,
    )
    results.append(("both", r))
    return results


def main():
    print("Fetching token…")
    token = None
    for label, r in get_token_variants():
        print(f"  [{label}] HTTP {r.status_code}  {r.text[:200]}")
        if r.status_code == 200 and "access_token" in (r.text or ""):
            token = r.json()["access_token"]
            print(f"  => got token via {label}")
            break
    if not token:
        print("Unable to obtain token. Aborting.")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}

    print("\n=== Fetch Swagger / OpenAPI spec ===")
    for path in [
        "/swagger/v1/swagger.json",
        "/swagger/index.html",
        "/swagger.json",
        "/openapi.json",
        "/api-docs",
        "/swagger",
        "/api/swagger",
        "/docs",
        "/redoc",
    ]:
        url = BASE + path
        r = requests.get(url, headers=headers, timeout=20)
        print(f"  GET {path:<30}  HTTP {r.status_code}  {len(r.content)} bytes  ct={r.headers.get('content-type','')[:30]}")
        if r.status_code == 200 and len(r.content) > 500:
            if "json" in r.headers.get("content-type", "") or r.text.lstrip().startswith("{"):
                out = Path("data") / ("spectrum_api_openapi" + path.replace("/", "_") + ".json")
                out.write_bytes(r.content)
                print(f"    saved -> {out}")
            elif "html" in r.headers.get("content-type", ""):
                out = Path("data") / ("spectrum_api_swagger" + path.replace("/", "_") + ".html")
                out.write_bytes(r.content)
                print(f"    saved -> {out}")

    print("\n=== Hit a few known endpoints to verify the bearer token works ===")
    for probe in [
        "/api",
        "/api/",
        "/api/ap/v1/apinvoice",
        "/api/AP/v1/apinvoice",
        "/api/jc/v1/job",
        "/api/JC/v1/job",
        "/api/v1/AP/apinvoice",
        "/api/v1/JC/job",
    ]:
        r = requests.get(BASE + probe, headers=headers, timeout=20)
        print(f"  GET {probe:<40}  HTTP {r.status_code}  {r.text[:150]}")


if __name__ == "__main__":
    main()
