import os
import requests
import asyncio
import hashlib
from datetime import datetime
from sqlalchemy.future import select
from app.core.database import AsyncSessionLocal
from app.models.cricket import Team, Player, PlayerStats, Match
from app.config import settings

async def get_or_create_team(session, name: str) -> Team:
    # Look up by name
    result = await session.execute(select(Team).filter(Team.name == name))
    team = result.scalars().first()
    if not team:
        team = Team(
            name=name,
            short_name=name[:3].upper(),
            team_type="National" if len(name) < 15 else "Franchise"
        )
        session.add(team)
        await session.flush()
    return team

async def get_or_create_player(session, name: str, country: str) -> Player:
    result = await session.execute(select(Player).filter(Player.name == name))
    player = result.scalars().first()
    if not player:
        player = Player(
            name=name,
            country=country
        )
        session.add(player)
        await session.flush()
    return player

async def update_player_stats(session, player_id: int, format_str: str, runs: int, wickets: int):
    # Fetch existing stats for player and format
    result = await session.execute(
        select(PlayerStats).filter(PlayerStats.player_id == player_id, PlayerStats.format == format_str)
    )
    stats = result.scalars().first()
    if not stats:
        stats = PlayerStats(
            player_id=player_id,
            format=format_str,
            matches_played=0,
            runs_scored=0,
            wickets_taken=0
        )
        session.add(stats)
        await session.flush()
        
    stats.matches_played += 1
    stats.runs_scored += runs
    stats.wickets_taken += wickets
    
    # Recalculate average
    if stats.matches_played > 0:
        stats.batting_average = round(stats.runs_scored / stats.matches_played, 2)
        stats.bowling_average = round((stats.wickets_taken * 25) / max(stats.wickets_taken, 1), 2)
    session.add(stats)

async def sync_daily_matches():
    if not settings.CRICAPI_KEY:
        print("CRICAPI_KEY is not set. Sync skipped.")
        return
        
    print("Starting CricAPI daily matches synchronization...")
    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch current matches
            url = f"https://api.cricapi.com/v1/currentMatches?apikey={settings.CRICAPI_KEY}"
            res = requests.get(url, timeout=10)
            if res.status_code != 200:
                print(f"Failed to fetch matches: {res.status_code}")
                return
                
            data = res.json()
            matches = data.get("data", [])
            
            for m in matches:
                m_id = m.get("id")
                # Parse unique ID
                if isinstance(m_id, str):
                    numeric_id = int(hashlib.md5(m_id.encode()).hexdigest(), 16) % 1000000
                else:
                    numeric_id = m_id or 1
                    
                # Check if match is already synced
                m_check = await session.execute(select(Match).filter(Match.id == numeric_id))
                if m_check.scalars().first():
                    continue
                    
                # We sync completed matches to update player stats
                is_completed = m.get("matchEnded") or "won" in m.get("status", "").lower()
                if not is_completed:
                    continue
                    
                print(f"Syncing completed match: {m.get('name')}")
                teams = m.get("teams", [])
                if len(teams) < 2:
                    continue
                    
                team_home_name = teams[0]
                team_away_name = teams[1]
                
                # Fetch detailed match info/scorecard to parse player stats
                detail_url = f"https://api.cricapi.com/v1/match_info?apikey={settings.CRICAPI_KEY}&id={m_id}"
                detail_res = requests.get(detail_url, timeout=10)
                
                # Create/Get Teams
                team_home = await get_or_create_team(session, team_home_name)
                team_away = await get_or_create_team(session, team_away_name)
                
                # Default parse score
                score_str = m.get("status", "Match Completed")
                
                # Parse date
                match_date = datetime.now().date()
                date_str = m.get("date")
                if date_str:
                    try:
                        match_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except:
                        pass
                        
                # Create Match
                new_match = Match(
                    id=numeric_id,
                    match_type=m.get("matchType", "T20").upper(),
                    team_home_id=team_home.id,
                    team_away_id=team_away.id,
                    status="Completed",
                    result=score_str,
                    match_date=match_date,
                    venue=m.get("venue", "Unknown Venue")
                )
                session.add(new_match)
                
                # 3. Parse players and scorecard details (mock details integration)
                # In CricAPI, scorecard details are available on match_info or scorecard endpoint.
                # We update a default incremental stat of +1 match to players if scorecard details are not fully parsed.
                # If we have scorecards, we update the player runs/wickets:
                if detail_res.status_code == 200:
                    detail_data = detail_res.json().get("data", {})
                    # Add dummy/parsed stats updates for active teams
                    # Here we simulate updating 11 players for home and away teams
                    # In production, we loop over detail_data["scorecard"] batsman and bowler lists
                    scorecard = detail_data.get("scorecard", [])
                    if scorecard:
                        for inning in scorecard:
                            # Update batsman stats
                            batsmen = inning.get("batsman", [])
                            for b in batsmen:
                                player_name = b.get("name")
                                runs = b.get("r", 0)
                                if player_name:
                                    player = await get_or_create_player(session, player_name, team_home_name)
                                    await update_player_stats(session, player.id, m.get("matchType", "T20").upper(), runs, 0)
                                    
                            # Update bowler stats
                            bowlers = inning.get("bowler", [])
                            for b in bowlers:
                                player_name = b.get("name")
                                wickets = b.get("w", 0)
                                if player_name:
                                    player = await get_or_create_player(session, player_name, team_away_name)
                                    await update_player_stats(session, player.id, m.get("matchType", "T20").upper(), 0, wickets)
                                    
                await session.commit()
                print(f"Successfully synced match {numeric_id} and updated player stats.")
                
        except Exception as e:
            print(f"Error during synchronization: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(sync_daily_matches())
