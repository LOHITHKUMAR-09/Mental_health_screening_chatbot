import asyncio
import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

async def test():
    from app.core.database import engine, Base
    from app.models import user, session, screening_response, risk_score, crisis_event
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("PostgreSQL connection: OK")
        print("All tables created successfully")
        
        # List tables
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
            tables = [row[0] for row in result.fetchall()]
            print(f"Tables in DB: {tables}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

asyncio.run(test())
