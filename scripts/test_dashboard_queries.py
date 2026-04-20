"""Run each tuned dashboard query against the real DB to verify they work."""
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.chdir(Path(__file__).resolve().parents[1])

from dotenv import load_dotenv
load_dotenv(".env")

from app.main import DASHBOARD_QUERIES
from app.db import run_query

for key, sql in DASHBOARD_QUERIES.items():
    print(f"\n== {key} ==")
    try:
        r = run_query(sql)
        print(f"  OK — {len(r['rows'])} rows, columns: {', '.join(r['columns'])}")
        if r["rows"]:
            first = r["rows"][0]
            print(f"  sample: {dict(list(first.items())[:4])}")
    except Exception as e:
        print(f"  FAIL: {e}")
