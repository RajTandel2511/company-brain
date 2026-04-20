"""Enumerate every SMB share on the NAS via DCERPC SRVSVC (NetShareEnum)."""
from smbprotocol.connection import Connection
from smbprotocol.session import Session
from smbprotocol.tree import TreeConnect
from smbprotocol.open import Open, CreateDisposition, CreateOptions, ImpersonationLevel, ShareAccess, FilePipePrinterAccessMask
from smbprotocol.ioctl import CtlCode, IOCTLFlags
import uuid, struct

from impacket.smbconnection import SMBConnection  # fallback easier API

HOST = "10.231.0.3"
USER = "rag_indexer"
PWD  = "North#121"

try:
    smb = SMBConnection(HOST, HOST)
    smb.login(USER, PWD)
    print("Shares visible to", USER, "on", HOST, ":")
    for s in smb.listShares():
        name = s["shi1_netname"][:-1] if isinstance(s["shi1_netname"], str) else s["shi1_netname"].decode().rstrip("\x00")
        remark = s["shi1_remark"]
        if not isinstance(remark, str):
            remark = remark.decode(errors="replace").rstrip("\x00")
        stype = s["shi1_type"]
        kind = {0: "Disk", 1: "Print", 2: "Device", 3: "IPC"}.get(stype & 0xFF, f"type{stype}")
        print(f"  [{kind:5}] {name:30} {remark}")
    smb.close()
except ImportError:
    print("Falling back to smbprotocol raw (no impacket installed)")
    conn = Connection(uuid.uuid4(), HOST, 445)
    conn.connect()
    session = Session(conn, USER, PWD)
    session.connect()
    tree = TreeConnect(session, rf"\\{HOST}\IPC$")
    tree.connect()
    print("connected via smbprotocol; but share enum needs SRVSVC RPC which is harder")
