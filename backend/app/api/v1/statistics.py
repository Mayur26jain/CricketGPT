from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.cricket import Player, PlayerStats, Team, Match
from app.schemas.stats import PlayerResponse, TeamResponse, MatchResponse
from typing import List, Optional

router = APIRouter()

@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player_details(player_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Player)
        .filter(Player.id == player_id)
        .options(selectinload(Player.stats))
    )
    player = result.scalars().first()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return player

@router.get("/players", response_model=List[PlayerResponse])
async def list_all_players(search: Optional[str] = None, ingest: bool = False, db: AsyncSession = Depends(get_db)):
    if search:
        # 1. Search database first
        result = await db.execute(
            select(Player)
            .filter(Player.name.ilike(f"%{search}%"))
            .options(selectinload(Player.stats))
        )
        players = list(result.scalars().all())
        
        # 2. Ingest/update if requested, or return quick search-only draft
        if ingest:
            from app.services.external_apis import ExternalAPIService
            from sqlalchemy import delete
            player_data = ExternalAPIService.search_and_import_player(search)
            
            if players:
                # Update existing player to correct country/styles
                db_player = players[0]
                db_player.name = player_data["name"]
                db_player.country = player_data["country"]
                db_player.batting_style = player_data["batting_style"]
                db_player.bowling_style = player_data["bowling_style"]
                
                # Delete old stats to avoid duplicates
                await db.execute(
                    delete(PlayerStats).filter(PlayerStats.player_id == db_player.id)
                )
            else:
                db_player = Player(
                    name=player_data["name"],
                    country=player_data["country"],
                    batting_style=player_data["batting_style"],
                    bowling_style=player_data["bowling_style"]
                )
                db.add(db_player)
                await db.flush()
                
            for stat in player_data["stats"]:
                db_stat = PlayerStats(
                    player_id=db_player.id,
                    format=stat["format"],
                    matches_played=stat["matches_played"],
                    innings_batted=stat["innings_batted"],
                    runs_scored=stat["runs_scored"],
                    highest_score=stat["highest_score"],
                    batting_average=stat["batting_average"],
                    strike_rate=stat["strike_rate"],
                    centuries=stat["centuries"],
                    half_centuries=stat["half_centuries"],
                    wickets_taken=stat["wickets_taken"],
                    bowling_average=stat["bowling_average"],
                    economy_rate=stat["economy_rate"],
                    best_bowling=stat["best_bowling"]
                )
                db.add(db_stat)
            
            await db.commit()
            
            # Re-query
            result = await db.execute(
                select(Player)
                .filter(Player.id == db_player.id)
                .options(selectinload(Player.stats))
            )
            players = [result.scalars().first()]
        elif not players:
            from app.services.external_apis import ExternalAPIService
            draft = ExternalAPIService.search_player_draft(search)
            if draft:
                players = [draft]
        return players

    result = await db.execute(
        select(Player)
        .options(selectinload(Player.stats))
    )
    return list(result.scalars().all())

@router.get("/teams", response_model=List[TeamResponse])
async def list_all_teams(search: Optional[str] = None, ingest: bool = False, db: AsyncSession = Depends(get_db)):
    if search:
        result = await db.execute(
            select(Team)
            .filter(Team.name.ilike(f"%{search}%"))
        )
        teams = list(result.scalars().all())
        
        if ingest:
            from app.services.external_apis import ExternalAPIService
            team_data = ExternalAPIService.search_and_import_team(search)
            
            if teams:
                db_team = teams[0]
                db_team.name = team_data["name"]
                db_team.short_name = team_data["short_name"]
                db_team.team_type = team_data["team_type"]
            else:
                db_team = Team(
                    name=team_data["name"],
                    short_name=team_data["short_name"],
                    team_type=team_data["team_type"]
                )
                db.add(db_team)
            await db.commit()
            
            result = await db.execute(select(Team).filter(Team.id == db_team.id))
            teams = [result.scalars().first()]
        elif not teams:
            from app.services.external_apis import ExternalAPIService
            draft = ExternalAPIService.search_team_draft(search)
            if draft:
                teams = [draft]
        return teams

    result = await db.execute(select(Team))
    return list(result.scalars().all())

@router.get("/teams/{team_id}/rankings")
async def get_team_icc_rankings(team_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Team).filter(Team.id == team_id))
    team = result.scalars().first()
    if not team:
         raise HTTPException(status_code=404, detail="Team not found")
    from app.services.external_apis import ExternalAPIService
    return ExternalAPIService.get_team_rankings(team.name)

@router.get("/matchup")
async def get_matchup_details(
    batsman_id: int, 
    bowler_id: int, 
    db: AsyncSession = Depends(get_db)
):
    # Fetch players
    batsman_res = await db.execute(select(Player).filter(Player.id == batsman_id))
    batsman = batsman_res.scalars().first()
    
    bowler_res = await db.execute(select(Player).filter(Player.id == bowler_id))
    bowler = bowler_res.scalars().first()
    
    if not batsman or not bowler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both players not found"
        )
    
    # 1. Search the matchup_cache table for real-world ball-by-ball Cricsheet records
    from app.models.cricket import MatchupCache
    
    batsman_surname = batsman.name.split()[-1].strip()
    bowler_surname = bowler.name.split()[-1].strip()
    
    cache_res = await db.execute(
        select(MatchupCache)
        .filter(
            MatchupCache.batsman_name.ilike(f"%{batsman_surname}%"),
            MatchupCache.bowler_name.ilike(f"%{bowler_surname}%")
        )
    )
    cache_entries = cache_res.scalars().all()
    
    def name_matches(full_name, cricsheet_name):
        full_name_clean = full_name.lower().replace("-", " ").strip()
        cricsheet_name_clean = cricsheet_name.lower().replace("-", " ").strip()
        if full_name_clean == cricsheet_name_clean:
            return True
        fn_parts = full_name_clean.split()
        cn_parts = cricsheet_name_clean.split()
        if not fn_parts or not cn_parts:
            return False
        if fn_parts[-1] != cn_parts[-1]:
            return False
        return fn_parts[0][0] == cn_parts[0][0]

    matching_entry = None
    for entry in cache_entries:
        if name_matches(batsman.name, entry.batsman_name) and name_matches(bowler.name, entry.bowler_name):
            matching_entry = entry
            break
            
    if matching_entry and matching_entry.balls > 0:
        runs = matching_entry.runs
        balls = matching_entry.balls
        dismissals = matching_entry.dismissals
        average = round(runs / dismissals, 2) if dismissals > 0 else runs
        strike_rate = round((runs / balls) * 100, 2) if balls > 0 else 0.0
        dots_pct = round((matching_entry.dots / balls) * 100) if balls > 0 else 0
        
        types = [
            {"name": "Caught", "value": matching_entry.caught, "color": "#4f73ff"},
            {"name": "Stumped", "value": matching_entry.stumped, "color": "#eab308"},
            {"name": "Bowled", "value": matching_entry.bowled, "color": "#db2777"},
            {"name": "LBW", "value": matching_entry.lbw, "color": "#10b981"}
        ]
        
        return {
            "batsman": batsman.name,
            "bowler": bowler.name,
            "runs": runs,
            "balls": balls,
            "dismissals": dismissals,
            "average": average,
            "strike_rate": strike_rate,
            "dots_pct": dots_pct,
            "fours": matching_entry.fours,
            "sixes": matching_entry.sixes,
            "dismissal_types": types
        }

    # 2. Fallback to career ratings calculation
    # Look up batsman stats to compute average career ratings
    batsman_stats_res = await db.execute(
        select(PlayerStats).filter(PlayerStats.player_id == batsman_id)
    )
    bat_stats = batsman_stats_res.scalars().all()
    
    bat_avg = 35.0
    bat_sr = 100.0
    if bat_stats:
        valid_avgs = [s.batting_average for s in bat_stats if s.batting_average > 0]
        if valid_avgs:
            bat_avg = sum(valid_avgs) / len(valid_avgs)
        valid_srs = [s.strike_rate for s in bat_stats if s.strike_rate > 0]
        if valid_srs:
            bat_sr = sum(valid_srs) / len(valid_srs)

    # Look up bowler stats to verify they are not a pure batsman and compute ratings
    stats_res = await db.execute(
        select(PlayerStats).filter(PlayerStats.player_id == bowler_id)
    )
    b_stats = stats_res.scalars().all()
    has_wickets = any(s.wickets_taken > 0 for s in b_stats)
    is_bowler = True
    if b_stats and not has_wickets:
        is_bowler = False

    bowl_avg = 28.0
    bowl_econ = 6.0
    if b_stats:
        valid_bowl_avgs = [s.bowling_average for s in b_stats if s.bowling_average > 0]
        if valid_bowl_avgs:
            bowl_avg = sum(valid_bowl_avgs) / len(valid_bowl_avgs)
        valid_econs = [s.economy_rate for s in b_stats if s.economy_rate > 0]
        if valid_econs:
            bowl_econ = sum(valid_econs) / len(valid_econs)

    from app.services.external_apis import ExternalAPIService
    return ExternalAPIService.generate_matchup_stats(
        batsman.name, 
        bowler.name, 
        is_bowler,
        bat_avg=bat_avg,
        bat_sr=bat_sr,
        bowl_avg=bowl_avg,
        bowl_econ=bowl_econ
    )

@router.get("/rankings")
async def get_icc_rankings():
    return {
        "Test": {
            "Teams": [
                {"rank": 1, "team": "Australia", "points": 131},
                {"rank": 2, "team": "South Africa", "points": 119},
                {"rank": 3, "team": "New Zealand", "points": 106},
                {"rank": 4, "team": "India", "points": 104},
                {"rank": 5, "team": "England", "points": 99}
            ],
            "Batsmen": [
                {"rank": 1, "player": "Kane Williamson", "rating": 859},
                {"rank": 2, "player": "Joe Root", "rating": 824},
                {"rank": 3, "player": "Steve Smith", "rating": 818}
            ]
        },
        "ODI": {
            "Teams": [
                {"rank": 1, "team": "India", "points": 116},
                {"rank": 2, "team": "New Zealand", "points": 109},
                {"rank": 3, "team": "Australia", "points": 102},
                {"rank": 4, "team": "South Africa", "points": 102},
                {"rank": 5, "team": "Pakistan", "points": 100}
            ],
            "Batsmen": [
                {"rank": 1, "player": "Babar Azam", "rating": 824},
                {"rank": 2, "player": "Shubman Gill", "rating": 801},
                {"rank": 3, "player": "Virat Kohli", "rating": 768}
            ]
        }
    }

