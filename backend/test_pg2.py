import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5433,
            user="mindease_user",
            password="mindease_password",
            database="mindease_db",
        )
        version = await conn.fetchval("SELECT version()")
        print(f"Connected! {version[:60]}")
        await conn.close()
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")

asyncio.run(test())
