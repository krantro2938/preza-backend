"""
Migration script to change topic column from VARCHAR(500) to TEXT
Run this script once to update the database schema
"""
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/ai_presentations")

async def migrate():
    """Change topic column from VARCHAR(500) to TEXT"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # PostgreSQL can convert VARCHAR to TEXT directly
        await conn.execute(
            text("""
            ALTER TABLE presentations 
            ALTER COLUMN topic TYPE TEXT
            """)
        )
    
    await engine.dispose()
    print("✅ Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
