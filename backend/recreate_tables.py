import asyncio
import sys
sys.path.insert(0, r"C:\Users\cheru\Documents\Projects\ML_Mental_Health_Screening\backend")

from app.core.database import engine, Base
from app.models import user, session, screening_response, risk_score, crisis_event

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Dropped old tables")
        await conn.run_sync(Base.metadata.create_all)
        print("Created all tables with timezone-aware columns")

asyncio.run(main())
