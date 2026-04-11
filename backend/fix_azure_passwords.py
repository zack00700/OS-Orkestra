"""
Fix passwords in Azure SQL Orkestra database.
Run: python fix_azure_passwords.py
"""
import hashlib
import hmac
import os
import base64

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return base64.b64encode(salt + key).decode("utf-8")

# Connect directly to Azure SQL
try:
    import pymssql
    conn = pymssql.connect(
        server="osmdm-server.database.windows.net",
        port=1433,
        user="mdm-admin",
        password=input("Mot de passe Azure SQL (mdm-admin): "),
        database="Orkestra",
        login_timeout=15,
    )
except ImportError:
    import pyodbc
    pwd = input("Mot de passe Azure SQL (mdm-admin): ")
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER=osmdm-server.database.windows.net,1433;"
        f"DATABASE=Orkestra;"
        f"UID=mdm-admin;PWD={pwd};"
        f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=15"
    )

cursor = conn.cursor()

# Hash Test1234 pour chaque user (chacun a un salt différent)
users = [
    "admin@opensid.com",
    "zack@opensid.com",
    "marketing@opensid.com",
    "commercial@opensid.com",
    "viewer@opensid.com",
]

for email in users:
    h = hash_password("Test1234")
    cursor.execute("UPDATE users SET hashed_password = %s WHERE email = %s", (h, email))
    print(f"  ✓ {email} → mot de passe mis à jour")

conn.commit()
cursor.close()
conn.close()

print("\nTerminé ! Login : admin@opensid.com / Test1234")
