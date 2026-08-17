import asyncio
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.cricket import Player, PlayerStats, Team

async def clear_bad_records():
    print("Connecting to database to purge dynamically cached records...")
    async with AsyncSessionLocal() as session:
        # Delete non-seeded players (id > 5)
        player_delete_q = await session.execute(
            select(Player).filter(Player.id > 5)
        )
        players_to_delete = player_delete_q.scalars().all()
        for p in players_to_delete:
            print(f"Purging bad player cache: {p.name}")
            await session.delete(p)
            
        # Delete non-seeded teams (id > 5)
        team_delete_q = await session.execute(
            select(Team).filter(Team.id > 5)
        )
        teams_to_delete = team_delete_q.scalars().all()
        for t in teams_to_delete:
            print(f"Purging bad team cache: {t.name}")
            await session.delete(t)
            
        await session.commit()
    print("Database purged successfully! All bad historical mappings cleared.")

if __name__ == "__main__":
    asyncio.run(clear_bad_records())
