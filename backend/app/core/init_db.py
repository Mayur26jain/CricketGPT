import asyncio
from datetime import date
from sqlalchemy.future import select
from sqlalchemy import delete
from app.core.database import Base, engine, AsyncSessionLocal
from app.models.user import User
from app.models.cricket import Team, Player, PlayerStats, Match
from app.core.security import get_password_hash

async def seed_data(db):
    print("Synchronizing and seeding database...")

    # Seed Teams list
    teams_to_seed = [
        Team(id=1, name="India", short_name="IND", team_type="National", logo_url="https://flagcdn.com/w160/in.png"),
        Team(id=2, name="Australia", short_name="AUS", team_type="National", logo_url="https://flagcdn.com/w160/au.png"),
        Team(id=3, name="England", short_name="ENG", team_type="National", logo_url="https://flagcdn.com/w160/gb-eng.png"),
        Team(id=4, name="Mumbai Indians", short_name="MI", team_type="Franchise", logo_url=""),
        Team(id=5, name="Chennai Super Kings", short_name="CSK", team_type="Franchise", logo_url=""),
        Team(id=6, name="Sri Lanka", short_name="SL", team_type="National", logo_url="https://flagcdn.com/w160/lk.png"),
        Team(id=7, name="Pakistan", short_name="PAK", team_type="National", logo_url="https://flagcdn.com/w160/pk.png"),
        Team(id=8, name="South Africa", short_name="SA", team_type="National", logo_url="https://flagcdn.com/w160/za.png"),
        Team(id=9, name="West Indies", short_name="WI", team_type="National", logo_url="https://flagcdn.com/w160/gp.png"),
        Team(id=10, name="Bangladesh", short_name="BAN", team_type="National", logo_url="https://flagcdn.com/w160/bd.png"),
        Team(id=11, name="New Zealand", short_name="NZ", team_type="National", logo_url="https://flagcdn.com/w160/nz.png"),
        Team(id=12, name="Afghanistan", short_name="AFG", team_type="National", logo_url="https://flagcdn.com/w160/af.png"),
        Team(id=13, name="Royal Challengers Bengaluru", short_name="RCB", team_type="Franchise", logo_url=""),
        Team(id=14, name="Kolkata Knight Riders", short_name="KKR", team_type="Franchise", logo_url=""),
        Team(id=15, name="Gujarat Titans", short_name="GT", team_type="Franchise", logo_url=""),
        Team(id=16, name="Rajasthan Royals", short_name="RR", team_type="Franchise", logo_url="")
    ]

    for t in teams_to_seed:
        res = await db.execute(select(Team).filter(Team.id == t.id))
        if not res.scalars().first():
            db.add(t)
    await db.flush()

    # Seed Players list (if none exist)
    res_players = await db.execute(select(Player).limit(1))
    if not res_players.scalars().first():
        kohli = Player(id=1, name="Virat Kohli", country="India", date_of_birth=date(1988, 11, 5), batting_style="Right-handed", bowling_style="Right-arm medium", image_url="")
        root = Player(id=2, name="Joe Root", country="England", date_of_birth=date(1990, 12, 30), batting_style="Right-handed", bowling_style="Right-arm offbreak", image_url="")
        tendulkar = Player(id=3, name="Sachin Tendulkar", country="India", date_of_birth=date(1973, 4, 24), batting_style="Right-handed", bowling_style="Right-arm legbreak", image_url="")
        smith = Player(id=4, name="Steve Smith", country="Australia", date_of_birth=date(1989, 6, 2), batting_style="Right-handed", bowling_style="Right-arm legbreak", image_url="")
        dhoni = Player(id=5, name="MS Dhoni", country="India", date_of_birth=date(1981, 7, 7), batting_style="Right-handed", bowling_style="Right-arm medium", image_url="")
        db.add_all([kohli, root, tendulkar, smith, dhoni])
        await db.flush()

        # Seed Player Stats
        stats = [
            PlayerStats(player_id=1, format="Test", matches_played=113, innings_batted=191, runs_scored=8848, highest_score=254, batting_average=49.15, strike_rate=55.56, centuries=29, half_centuries=30, wickets_taken=0, bowling_average=0.0, economy_rate=3.0, best_bowling="0/0"),
            PlayerStats(player_id=1, format="ODI", matches_played=292, innings_batted=280, runs_scored=13848, highest_score=183, batting_average=58.67, strike_rate=93.54, centuries=50, half_centuries=72, wickets_taken=4, bowling_average=166.2, economy_rate=6.2, best_bowling="1/15"),
            PlayerStats(player_id=1, format="IPL", matches_played=252, innings_batted=244, runs_scored=8004, highest_score=113, batting_average=38.66, strike_rate=131.97, centuries=8, half_centuries=55, wickets_taken=4, bowling_average=92.0, economy_rate=8.8, best_bowling="2/25"),
            PlayerStats(player_id=2, format="Test", matches_played=140, innings_batted=256, runs_scored=11736, highest_score=262, batting_average=50.15, strike_rate=56.78, centuries=32, half_centuries=62, wickets_taken=69, bowling_average=44.20, economy_rate=3.2, best_bowling="5/8"),
            PlayerStats(player_id=2, format="ODI", matches_played=171, innings_batted=160, runs_scored=6522, highest_score=133, batting_average=47.60, strike_rate=86.75, centuries=16, half_centuries=38, wickets_taken=26, bowling_average=57.38, economy_rate=5.7, best_bowling="2/31"),
            PlayerStats(player_id=3, format="Test", matches_played=200, innings_batted=329, runs_scored=15921, highest_score=248, batting_average=53.78, strike_rate=54.00, centuries=51, half_centuries=68, wickets_taken=46, bowling_average=54.17, economy_rate=3.5, best_bowling="3/10"),
            PlayerStats(player_id=3, format="ODI", matches_played=463, innings_batted=452, runs_scored=18426, highest_score=200, batting_average=44.83, strike_rate=86.23, centuries=49, half_centuries=96, wickets_taken=154, bowling_average=44.48, economy_rate=4.8, best_bowling="5/32"),
            PlayerStats(player_id=4, format="Test", matches_played=109, innings_batted=195, runs_scored=9685, highest_score=239, batting_average=56.97, strike_rate=53.50, centuries=32, half_centuries=41, wickets_taken=19, bowling_average=55.47, economy_rate=3.4, best_bowling="3/18"),
            PlayerStats(player_id=4, format="ODI", matches_played=155, innings_batted=139, runs_scored=5446, highest_score=164, batting_average=43.91, strike_rate=87.35, centuries=12, half_centuries=33, wickets_taken=28, bowling_average=38.45, economy_rate=5.4, best_bowling="3/24")
        ]
        db.add_all(stats)
        await db.flush()

    # IMPORTANT:
    # Never delete historical matches here.
    # Historical matches are managed by the Cricket data loader.
    # Demo/live matches are added only if their IDs do not already exist.

    # Dynamic team lookups to avoid collision with existing database team IDs
    async def get_or_create_team_id(name: str, short_name: str, team_type: str = "National") -> int:
        res = await db.execute(select(Team).filter(Team.name == name))
        existing = res.scalars().first()
        if existing:
            return existing.id
        
        res_short = await db.execute(select(Team).filter(Team.short_name == short_name))
        existing_short = res_short.scalars().first()
        if existing_short:
            return existing_short.id

        new_team = Team(name=name, short_name=short_name, team_type=team_type)
        db.add(new_team)
        await db.flush()
        return new_team.id

    sl_id = await get_or_create_team_id("Sri Lanka", "SL", "National")
    ind_id = await get_or_create_team_id("India", "IND", "National")
    pak_id = await get_or_create_team_id("Pakistan", "PAK", "National")
    sa_id = await get_or_create_team_id("South Africa", "SA", "National")
    aus_id = await get_or_create_team_id("Australia", "AUS", "National")
    eng_id = await get_or_create_team_id("England", "ENG", "National")
    mi_id = await get_or_create_team_id("Mumbai Indians", "MI", "Franchise")
    csk_id = await get_or_create_team_id("Chennai Super Kings", "CSK", "Franchise")
    wi_id = await get_or_create_team_id("West Indies", "WI", "National")
    ban_id = await get_or_create_team_id("Bangladesh", "BAN", "National")
    nz_id = await get_or_create_team_id("New Zealand", "NZ", "National")
    afg_id = await get_or_create_team_id("Afghanistan", "AFG", "National")
    rcb_id = await get_or_create_team_id("Royal Challengers Bengaluru", "RCB", "Franchise")
    kkr_id = await get_or_create_team_id("Kolkata Knight Riders", "KKR", "Franchise")
    gt_id = await get_or_create_team_id("Gujarat Titans", "GT", "Franchise")
    rr_id = await get_or_create_team_id("Rajasthan Royals", "RR", "Franchise")

    matches_to_seed = [
        Match(id=1, match_type="T20", team_home_id=sl_id, team_away_id=ind_id, status="Live", match_date=date(2026, 8, 11), venue="R. Premadasa Stadium, Colombo"),
        Match(id=2, match_type="Test", team_home_id=pak_id, team_away_id=sa_id, status="Live", match_date=date(2026, 8, 10), venue="Gaddafi Stadium, Lahore"),
        Match(id=3, match_type="T20", team_home_id=aus_id, team_away_id=eng_id, status="Live", match_date=date(2026, 8, 10), venue="Melbourne Cricket Ground, Melbourne"),
        Match(id=4, match_type="T20", team_home_id=mi_id, team_away_id=csk_id, status="Live", match_date=date(2026, 8, 10), venue="Wankhede Stadium, Mumbai"),
        Match(id=5, match_type="ODI", team_home_id=wi_id, team_away_id=ban_id, status="Upcoming", match_date=date(2026, 8, 12), venue="Kensington Oval, Barbados"),
        Match(id=6, match_type="Test", team_home_id=nz_id, team_away_id=afg_id, status="Upcoming", match_date=date(2026, 8, 13), venue="Eden Park, Auckland"),
        Match(id=7, match_type="T20", team_home_id=rcb_id, team_away_id=kkr_id, status="Upcoming", match_date=date(2026, 8, 11), venue="M. Chinnaswamy Stadium, Bengaluru"),
        Match(id=8, match_type="ODI", team_home_id=ind_id, team_away_id=aus_id, status="Completed", result="Australia won by 6 wickets", match_date=date(2026, 8, 9), venue="Narendra Modi Stadium, Ahmedabad"),
        Match(id=9, match_type="Test", team_home_id=eng_id, team_away_id=sa_id, status="Completed", result="England won by 115 runs", match_date=date(2026, 8, 8), venue="Lord's, London"),
        Match(id=10, match_type="T20", team_home_id=gt_id, team_away_id=rr_id, status="Completed", result="Rajasthan Royals won by 3 wickets", match_date=date(2026, 8, 7), venue="Narendra Modi Stadium, Ahmedabad")
    ]
    # Add demo matches only when they do not already exist.
    # Never overwrite/delete historical CricketGPT matches.
    for match in matches_to_seed:
        res_match = await db.execute(
            select(Match).filter(Match.id == match.id)
        )
        if not res_match.scalars().first():
            db.add(match)

    await db.flush()
    
    # Seed a Demo User if none exists
    res_user = await db.execute(select(User).filter(User.email == "demo@cricketgpt.com"))
    if not res_user.scalars().first():
        demo_user = User(
            email="demo@cricketgpt.com",
            password_hash=get_password_hash("password123"),
            full_name="Demo User",
            preferred_language="en",
            is_active=True
        )
        db.add(demo_user)
        
    await db.commit()
    print("Database seeding completed.")

async def init_db():
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        await seed_data(session)

if __name__ == "__main__":
    asyncio.run(init_db())
