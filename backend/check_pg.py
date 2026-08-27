import asyncio, asyncpg

async def main():
    tests = [
        ("localhost", 5432, "postgres", "", "postgres"),
        ("localhost", 5432, "postgres", "postgres", "postgres"),
        ("localhost", 5432, "postgres", "admin", "postgres"),
        ("localhost", 5432, "mindease_user", "mindease_password", "postgres"),
    ]
    for host, port, user, pwd, db in tests:
        try:
            conn = await asyncpg.connect(host=host, port=port, user=user,
                                          password=pwd or None, database=db, timeout=3)
            v = await conn.fetchval("SELECT version()")
            print(f"SUCCESS user={user}: {v[:60]}")
            rows = await conn.fetch("SELECT datname FROM pg_database WHERE datistemplate=false")
            print(f"  DBs: {[r['datname'] for r in rows]}")
            await conn.close()
        except Exception as e:
            print(f"FAIL user={user}: {type(e).__name__}: {str(e)[:80]}")

asyncio.run(main())
