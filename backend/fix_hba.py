import os

hba_path = r"C:\Program Files\PostgreSQL\16\data\pg_hba.conf"
content = """# PostgreSQL Client Authentication Configuration File
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust
"""

with open(hba_path, "wb") as f:
    f.write(content.encode("ascii"))

print("pg_hba.conf written in pure ASCII")
