import asyncio, sys, traceback
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

async def main():
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import create_access_token

    async with AsyncSessionLocal() as db:
        try:
            user = User(role="student", is_anonymous=True)
            db.add(user)
            await db.flush()
            print(f"User created: id={user.id}")
            token = create_access_token({"sub": str(user.id), "role": "student", "anon": True})
            print(f"Token OK: {token[:40]}...")
            await db.commit()
            print("Commit OK")
        except Exception as e:
            traceback.print_exc()

asyncio.run(main())
