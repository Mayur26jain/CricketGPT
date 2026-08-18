import sys
import os
import asyncio
from sqlalchemy.future import select

# Add backend directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from app.core.database import AsyncSessionLocal
from app.models.cricket import Player, PlayerStats, MatchupCache, Team, Match

async def verify():
    async with AsyncSessionLocal() as session:
        players = (await session.execute(select(Player))).scalars().all()
        stats = (await session.execute(select(PlayerStats))).scalars().all()
        matchups = (await session.execute(select(MatchupCache))).scalars().all()
        teams = (await session.execute(select(Team))).scalars().all()
        matches = (await session.execute(select(Match))).scalars().all()
        
        print("--- POSTGRESQL DATABASE VERIFICATION ---")
        print("Teams count:", len(teams))
        print("Players count:", len(players))
        print("Matches count:", len(matches))
        print("Player stats profiles:", len(stats))
        print("Batsman-vs-Bowler matchups:", len(matchups))
        print("-----------------------------------------")

if __name__ == "__main__":
    asyncio.run(verify())
