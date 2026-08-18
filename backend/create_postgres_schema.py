import asyncio

from app.core.database import Base, engine
import app.models.user
import app.models.cricket


async def main():
    print("Creating PostgreSQL schema...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()

    print("PostgreSQL schema created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
