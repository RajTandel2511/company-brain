"""Construct a SOAP envelope and POST to /ws. Discover the auth requirements."""
import requests
from pathlib import Path

BASE = "https://allairmechanical.dexterchaney.com:8482"
tok = requests.post(BASE + "/connect/token", data={
    "grant_type": "client_credentials",
    "client_id": "Spectrum-EB9A4694F",
    "client_secret": "4E070A9D-9C7C-4248-AC43-6698FE7C7CC2",
    "scope": "spectrumapi",
}, timeout=15).json()["access_token"]

def post_soap(envelope: str, soapaction: str = "", ct: str = "text/xml; charset=utf-8"):
    r = requests.post(
        BASE + "/ws",
        headers={
            "Authorization": f"Bearer {tok}",
            "Content-Type": ct,
            "SOAPAction": soapaction,
        },
        data=envelope.encode("utf-8"),
        timeout=30,
    )
    print(f"  HTTP {r.status_code}  ct={r.headers.get('content-type','')[:40]}  len={len(r.content)}")
    print(f"  body: {r.text[:800]!r}")

# 1. Naked SOAP envelope — see what error comes back
env1 = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Ping/>
  </soap:Body>
</soap:Envelope>"""
print("Test 1: naked envelope, no auth header")
post_soap(env1)

# 2. With a Spectrum-style Authorization SOAP header
env2 = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <Authorization xmlns="http://www.dexterchaney.com/Spectrum/Internal">
      <AuthorizationID>Integration</AuthorizationID>
    </Authorization>
  </soap:Header>
  <soap:Body>
    <Ping xmlns="http://www.dexterchaney.com/Spectrum/Internal"/>
  </soap:Body>
</soap:Envelope>"""
print("\nTest 2: with AuthorizationID Integration")
post_soap(env2)

# 3. Try fetching WSDL — SOAP services usually expose ?wsdl
print("\nTest 3: GET /ws?wsdl")
r = requests.get(BASE + "/ws?wsdl", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
print(f"  HTTP {r.status_code}  len={len(r.content)}")
if r.status_code == 200 and len(r.content) > 500:
    Path("data/spectrum_wsdl.xml").write_bytes(r.content)
    print("  saved to data/spectrum_wsdl.xml")
    print(f"  first 800 chars: {r.text[:800]}")

# 4. Try with SOAP 1.2 content type
print("\nTest 4: SOAP 1.2 content type")
post_soap(env1, ct="application/soap+xml; charset=utf-8")

# 5. Try real Spectrum service: CustomerInquiry
env5 = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SOAP-ENV:Header>
    <Authorization xmlns="http://www.dexterchaney.com/Spectrum/Integration">
      <Auth_ID>Integration</Auth_ID>
      <Operator_Code>RT1</Operator_Code>
      <Company_Code>AA1</Company_Code>
    </Authorization>
  </SOAP-ENV:Header>
  <SOAP-ENV:Body>
    <CustomerInquiry xmlns="http://www.dexterchaney.com/Spectrum/Integration">
      <Customer_Code>VCCLLC</Customer_Code>
      <Company_Code>AA1</Company_Code>
    </CustomerInquiry>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""
print("\nTest 5: real CustomerInquiry for VCCLLC")
post_soap(env5, soapaction="CustomerInquiry")
