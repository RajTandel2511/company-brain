"""Fetch the Jersey WADL from Spectrum — it enumerates every web service."""
import requests
from pathlib import Path

BASE = "https://allairmechanical.dexterchaney.com:8482"
r = requests.post(
    BASE + "/connect/token",
    data={"grant_type": "client_credentials", "client_id": "Spectrum-EB9A4694F",
          "client_secret": "4E070A9D-9C7C-4248-AC43-6698FE7C7CC2", "scope": "spectrumapi"},
    timeout=15,
)
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}

# WADL on /ws
r = requests.options(BASE + "/ws", headers=H, timeout=30)
wadl_path = Path("data/spectrum_wadl.xml")
wadl_path.write_bytes(r.content)
print(f"WADL saved: {len(r.content)} bytes -> {wadl_path}")

# Print a condensed view of every resource
import xml.etree.ElementTree as ET
ns = {"w": "http://wadl.dev.java.net/2009/02"}
root = ET.fromstring(r.content)

def walk(el, parent_path=""):
    path = el.attrib.get("path", "")
    full = (parent_path + "/" + path).replace("//", "/") if path else parent_path
    for method in el.findall("w:method", ns):
        print(f"  {method.attrib.get('name'):6} {full}  id={method.attrib.get('id','')}")
    for child in el.findall("w:resource", ns):
        walk(child, full)

for resources in root.findall("w:resources", ns):
    base = resources.attrib.get("base", "")
    print(f"\nBase: {base}")
    for resource in resources.findall("w:resource", ns):
        walk(resource)
