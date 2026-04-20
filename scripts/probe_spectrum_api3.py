"""Probe /ws with POST to find service names and surface a document endpoint."""
import json
import requests

BASE = "https://allairmechanical.dexterchaney.com:8482"
r = requests.post(
    BASE + "/connect/token",
    data={"grant_type": "client_credentials", "client_id": "Spectrum-EB9A4694F",
          "client_secret": "4E070A9D-9C7C-4248-AC43-6698FE7C7CC2", "scope": "spectrumapi"},
    timeout=15,
)
token = r.json()["access_token"]
print(f"Token OK")
H = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def probe(method: str, path: str, body=None):
    try:
        if method == "POST":
            r = requests.post(BASE + path, headers=H, json=body or {}, timeout=20)
        elif method == "OPTIONS":
            r = requests.options(BASE + path, headers=H, timeout=20)
        elif method == "HEAD":
            r = requests.head(BASE + path, headers=H, timeout=20)
        else:
            r = requests.get(BASE + path, headers=H, timeout=20)
        print(f"  {method:5} {r.status_code}  {path:<50}  {r.text[:200]!r}")
        return r
    except Exception as e:
        print(f"  {method:5} ERR   {path:<50}  {e}")


print("=== OPTIONS + HEAD on /ws ===")
probe("OPTIONS", "/ws")
probe("HEAD", "/ws")
probe("GET", "/ws/")
probe("POST", "/ws")
probe("POST", "/ws/")

print("\n=== POST /ws/<service> — common Spectrum service names ===")
for svc in [
    "Customer", "CustomerInquiry", "CustomerList", "CustomerRead",
    "APInvoice", "APInvoiceInquiry", "APInvoiceList", "APInvoiceRead",
    "Job", "JobInquiry", "JobMaster", "JobMasterInquiry",
    "Vendor", "VendorInquiry", "VendorMaster", "VendorList",
    "DIMaster", "DIImage", "DIImageMaster", "DI", "Image",
    "Document", "DocumentInquiry", "DocumentImaging",
    "GetDocument", "GetImage",
]:
    probe("POST", f"/ws/{svc}", {"company_code": "AA1"})
