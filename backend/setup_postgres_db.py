import asyncio
import asyncpg

async def main():
    # Connect as postgres user (now trusted locally)
    conn = await asyncpg.connect(host="localhost", port=5432, user="postgres", database="postgres")
    
    # Check if user exists
    user_exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = 'mindease_user'")
    if not user_exists:
        await conn.execute("CREATE USER mindease_user WITH PASSWORD 'mindease_password' SUPERUSER")
        print("Created user: mindease_user")
    else:
        await conn.execute("ALTER USER mindease_user WITH PASSWORD 'mindease_password' SUPERUSER")
        print("Updated user: mindease_user with password")

    # Check if database exists
    db_exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'mindease_db'")
    if not db_exists:
        await conn.execute("CREATE DATABASE mindease_db OWNER mindease_user")
        print("Created database: mindease_db")
    else:
        print("Database mindease_db already exists")

    await conn.close()

    # Now verify connection directly to mindease_db with mindease_user
    mconn = await asyncpg.connect(host="localhost", port=5432, user="mindease_user", password="mindease_password", database="mindease_db")
    print("Successfully connected as mindease_user to mindease_db!")
    await mconn.close()

asyncio.run(main())
