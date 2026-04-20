"""What server-level rights does AA1USER have, and can we OPENROWSET BULK?"""
import os
from pathlib import Path
import pyodbc
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.environ['SPECTRUM_SQL_HOST']},1433;"
    f"DATABASE={os.environ['SPECTRUM_SQL_DATABASE']};"
    f"UID={os.environ['SPECTRUM_SQL_USER']};PWD={os.environ['SPECTRUM_SQL_PASSWORD']};"
    "Encrypt=yes;TrustServerCertificate=yes;",
    timeout=10,
)
cur = conn.cursor()

print("=== Login info ===")
cur.execute("SELECT SUSER_NAME() AS login_name, SYSTEM_USER AS sysuser, @@VERSION AS ver")
row = cur.fetchone()
print(f"  login = {row.login_name}")
print(f"  server version (trimmed) = {row.ver[:80]}")

print("\n=== Server-level roles for this login ===")
cur.execute("""
    SELECT p.name AS principal, r.name AS role_name
    FROM sys.server_role_members rm
    JOIN sys.server_principals r ON r.principal_id = rm.role_principal_id
    JOIN sys.server_principals p ON p.principal_id = rm.member_principal_id
    WHERE p.name = SUSER_NAME()
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  {r.principal} -> {r.role_name}")
else:
    print("  (none)")

print("\n=== Explicit server-level permissions ===")
try:
    cur.execute("""
        SELECT class_desc, permission_name, state_desc
        FROM sys.server_permissions sp
        JOIN sys.server_principals p ON p.principal_id = sp.grantee_principal_id
        WHERE p.name = SUSER_NAME()
    """)
    for row in cur.fetchall():
        print(f"  {row.class_desc:<20} {row.permission_name:<30} {row.state_desc}")
except Exception as e:
    print(f"  (denied: {e})")

print("\n=== Database-level roles ===")
cur.execute("""
    SELECT r.name AS role_name
    FROM sys.database_role_members rm
    JOIN sys.database_principals r ON r.principal_id = rm.role_principal_id
    JOIN sys.database_principals p ON p.principal_id = rm.member_principal_id
    WHERE p.name = USER_NAME()
""")
for row in cur.fetchall():
    print(f"  {row.role_name}")

print("\n=== HAS_PERMS_BY_NAME checks ===")
for perm in ["ADMINISTER BULK OPERATIONS", "CONTROL SERVER", "ALTER ANY LOGIN",
             "VIEW SERVER STATE", "ALTER SETTINGS"]:
    try:
        cur.execute(f"SELECT HAS_PERMS_BY_NAME(NULL, NULL, '{perm}') AS has_it")
        has = cur.fetchone().has_it
        print(f"  {perm:<30} -> {has}")
    except Exception as e:
        print(f"  {perm:<30} ERR {e}")

print("\n=== Try OPENROWSET BULK on a known DI image path ===")
try:
    cur.execute("""
        SELECT TOP 1 Image_Path, Image_Filename, Document_ID
        FROM dbo.DI_IMAGE_MASTER
        WHERE Image_Path IS NOT NULL AND LEN(LTRIM(RTRIM(Image_Path))) > 0
          AND Image_Filename LIKE '%.pdf'
    """)
    sample = cur.fetchone()
    full = (sample.Image_Path.strip() + sample.Image_Filename.strip())
    print(f"  target: {full}")
    # Try pulling just the length
    sql = (
        "SELECT DATALENGTH(BulkColumn) AS n "
        f"FROM OPENROWSET(BULK N'{full}', SINGLE_BLOB) AS x"
    )
    cur.execute(sql)
    n = cur.fetchone().n
    print(f"  SUCCESS — SQL can see the file. bytes={n:,}")
except Exception as e:
    print(f"  NOPE ({e})")

print("\n=== Try xp_cmdshell ===")
try:
    cur.execute("EXEC xp_cmdshell 'dir D:\\Images\\AA1\\ 2>&1'")
    for row in cur.fetchall():
        if row[0]: print(f"  {row[0]}")
except Exception as e:
    print(f"  NOPE ({e})")

print("\n=== Try xp_dirtree ===")
try:
    cur.execute("EXEC master.sys.xp_dirtree 'D:\\Images\\AA1', 1, 1")
    for row in cur.fetchall():
        print(f"  {row}")
except Exception as e:
    print(f"  NOPE ({e})")
