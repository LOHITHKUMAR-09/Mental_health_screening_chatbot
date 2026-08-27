import asyncio
import asyncpg

async def check_pg():
    # Test default postgres user (native Windows PG usually uses Windows auth or postgres superuser)
    tests = [
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "", "db": "postgres"},
        {"host": "localhost", "port": 5432, "user": "postgres", "password": "postgres", "db": "postgres"},
    ]
    for t in tests:
        try:
            conn = await asyncpg.connect(host=t["host"], port=t["port"], user=t["user"], 
                                         password=t["password"] or None, database=t["db"])
            v = await conn.fetchval("SELECT version()")
            print(f"Connected as {t['user']}@{t['port']}: {v[:50]}")
            
            # Check if mindease_db exists
            dbs = await conn.fetch("SELECT datname FROM pg_database")
            db_names = [r["datname"] for r in dbs]
            print(f"Databases: {db_names}")
            
            if "mindease_db" not in db_names:
                print("Creating mindease_db and mindease_user...")
                await conn.execute("CREATE USER mindease_user WITH PASSWORD 'mindease_password'")
                await conn.execute("CREATE DATABASE mindease_db OWNER mindease_user")
                print("Done")
            else:
                print("mindease_db already exists")
            await conn.close()
            return True
        except Exception as e:
            print(f"  FAILED {t['user']}@{t['port']}: {type(e).__name__}: {e}")
    return False

asyncio.run(check_pg())
