import os
import sys
import asyncio
import time
from datetime import datetime
from sqlalchemy.future import select

# Add parent directory to sys.path to enable app module imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

from app.core.database import AsyncSessionLocal, engine
from app.models.cricket import Team, Player, PlayerStats, MatchupCache, Match

DATASET_DIR = os.path.join(PROJECT_ROOT, "Archive", "criket-data")

IPL_SHORT_NAMES = {
    "Chennai Super Kings": "CSK",
    "Delhi Capitals": "DC",
    "Delhi Daredevils": "DD",
    "Kings XI Punjab": "KXIP",
    "Punjab Kings": "PBKS",
    "Kolkata Knight Riders": "KKR",
    "Mumbai Indians": "MI",
    "Rajasthan Royals": "RR",
    "Royal Challengers Bangalore": "RCB",
    "Royal Challengers Bengaluru": "RCB",
    "Sunrisers Hyderabad": "SRH",
    "Deccan Chargers": "DC",
    "Kochi Tuskers Kerala": "KTK",
    "Pune Warriors": "PWI",
    "Rising Pune Supergiants": "RPS",
    "Rising Pune Supergiant": "RPS",
    "Gujarat Lions": "GL",
    "Gujarat Titans": "GT",
    "Lucknow Super Giants": "LSG"
}

def get_short_name(team_name):
    if team_name in IPL_SHORT_NAMES:
        return IPL_SHORT_NAMES[team_name]
    words = team_name.split()
    if len(words) >= 2:
        return "".join([w[0].upper() for w in words])
    return team_name[:3].upper()

def parse_match_info(filepath):
    info = {
        "competition": "",
        "date": None,
        "venue": None,
        "team_home": None,
        "team_away": None,
        "winner": None,
        "result": None,
        "match_type": "T20"
    }
    
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    i = 0
    n = len(lines)
    teams = []
    
    while i < n:
        line = lines[i]
        if line.startswith("info:"):
            i += 1
            while i < n and (lines[i].startswith("  ") or not lines[i].strip()):
                sub_line = lines[i].strip()
                if sub_line.startswith("competition:"):
                    info["competition"] = sub_line.split(":", 1)[1].strip()
                elif sub_line.startswith("match_type:"):
                    info["match_type"] = sub_line.split(":", 1)[1].strip()
                elif sub_line.startswith("venue:"):
                    info["venue"] = sub_line.split(":", 1)[1].strip()
                elif sub_line.startswith("outcome:"):
                    j = i + 1
                    while j < n and lines[j].startswith("    "):
                        if lines[j].strip().startswith("winner:"):
                            info["winner"] = lines[j].strip().split(":", 1)[1].strip()
                            info["result"] = f"Won by {info['winner']}"
                        j += 1
                elif sub_line.startswith("dates:"):
                    j = i + 1
                    if j < n and lines[j].strip().startswith("-"):
                        info["date"] = lines[j].strip().replace("-", "", 1).strip()
                elif sub_line.startswith("teams:"):
                    j = i + 1
                    while j < n and lines[j].strip().startswith("-"):
                        teams.append(lines[j].strip().replace("-", "", 1).strip())
                        j += 1
                i += 1
            break
        i += 1
        
    if len(teams) >= 2:
        info["team_home"] = teams[0]
        info["team_away"] = teams[1]
        
    for k, v in info.items():
        if isinstance(v, str):
            info[k] = v.strip("'\"")
            
    return info

def parse_match_players(filepath):
    players = {}
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("  players:"):
            i += 1
            current_team = None
            while i < n and (lines[i].startswith("    ") or not lines[i].strip()):
                sub_line = lines[i]
                if not sub_line.strip():
                    i += 1
                    continue
                if sub_line.startswith("    - "):
                    player_name = sub_line.strip().replace("- ", "", 1).strip()
                    player_name = player_name.strip("'\"")
                    if current_team:
                        players[current_team].append(player_name)
                elif sub_line.startswith("    ") and not sub_line.startswith("     "):
                    current_team = sub_line.strip().rstrip(":").strip()
                    current_team = current_team.strip("'\"")
                    players[current_team] = []
                i += 1
            break
        i += 1
    return players

def fast_parse_deliveries_full(filepath):
    deliveries = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("    - ") or (line.strip().startswith("- ") and "." in line):
            batsman = ""
            bowler = ""
            runs_batsman = 0
            runs_extras = 0
            runs_total = 0
            wides = 0
            noballs = 0
            byes = 0
            legbyes = 0
            wicket_kind = ""
            player_out = ""
            
            i += 1
            while i < n and not lines[i].startswith("    - ") and not lines[i].startswith("  - ") and not lines[i].startswith("info:") and not lines[i].startswith("meta:"):
                raw_line = lines[i]
                leading_spaces = len(raw_line) - len(raw_line.lstrip())
                sub_line = raw_line.strip()
                
                if sub_line.startswith("batsman:") and leading_spaces == 8:
                    batsman = sub_line.split(":", 1)[1].strip().strip("'\"")
                elif sub_line.startswith("bowler:") and leading_spaces == 8:
                    bowler = sub_line.split(":", 1)[1].strip().strip("'\"")
                elif sub_line.startswith("wides:"):
                    try:
                        wides = int(sub_line.split(":", 1)[1].strip())
                    except Exception:
                        wides = 1
                elif sub_line.startswith("noballs:"):
                    try:
                        noballs = int(sub_line.split(":", 1)[1].strip())
                    except Exception:
                        noballs = 1
                elif sub_line.startswith("byes:"):
                    try:
                        byes = int(sub_line.split(":", 1)[1].strip())
                    except Exception:
                        byes = 1
                elif sub_line.startswith("legbyes:"):
                    try:
                        legbyes = int(sub_line.split(":", 1)[1].strip())
                    except Exception:
                        legbyes = 1
                elif sub_line.startswith("wicket:"):
                    j = i + 1
                    while j < n and lines[j].startswith("        "):
                        sub_sub = lines[j].strip()
                        if sub_sub.startswith("kind:"):
                            wicket_kind = sub_sub.split(":", 1)[1].strip()
                        elif sub_sub.startswith("player_out:"):
                            player_out = sub_sub.split(":", 1)[1].strip().strip("'\"")
                        j += 1
                elif sub_line.startswith("runs:"):
                    j = i + 1
                    while j < n and lines[j].startswith("        "):
                        sub_sub = lines[j].strip()
                        if sub_sub.startswith("batsman:"):
                            try:
                                runs_batsman = int(sub_sub.split(":", 1)[1].strip())
                            except Exception:
                                pass
                        elif sub_sub.startswith("extras:"):
                            try:
                                runs_extras = int(sub_sub.split(":", 1)[1].strip())
                            except Exception:
                                pass
                        elif sub_sub.startswith("total:"):
                            try:
                                runs_total = int(sub_sub.split(":", 1)[1].strip())
                            except Exception:
                                pass
                        j += 1
                i += 1
            if batsman and bowler:
                deliveries.append({
                    "batsman": batsman,
                    "bowler": bowler,
                    "runs_batsman": runs_batsman,
                    "runs_extras": runs_extras,
                    "runs_total": runs_total,
                    "wides": wides,
                    "noballs": noballs,
                    "byes": byes,
                    "legbyes": legbyes,
                    "wicket_kind": wicket_kind,
                    "player_out": player_out
                })
        else:
            i += 1
    return deliveries

async def main():
    print("==================================================")
    print("  CricketGPT SQLAlchemy 2.0 Incremental Loader   ")
    print("==================================================")
    
    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset directory not found at: {DATASET_DIR}")
        return
        
    print(f"Scanning match files from subfolders in: {DATASET_DIR}")
    folders = [
        "bbl",
        "cpl",
        "ipl",
        "it20s",
        "mdms",
        "ntb",
        "odis",
        "odms",
        "psl",
        "t20s",
        "tests",
        "wbb"
    ]
    files = []
    for folder in folders:
        folder_path = os.path.join(DATASET_DIR, folder)
        if os.path.exists(folder_path):
            files.extend([(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".yaml")])
    print(f"Found {len(files)} match files across {', '.join(folders)}.")
    
    t0 = time.time()
    loaded_matches = 0
    skipped_matches = 0
    
    # Load maps from DB to resolve cache
    print("Connecting to database and fetching entity maps...")
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Team))
        teams_db = {t.name: t.id for t in res.scalars().all()}
        
        res = await session.execute(select(Player))
        players_db = {p.name: p.id for p in res.scalars().all()}
    print(f"Loaded {len(teams_db)} teams and {len(players_db)} players from database.")
    
    BATCH_SIZE = 500
    total_files = len(files)
    
    for chunk_start in range(0, total_files, BATCH_SIZE):
        chunk_files = files[chunk_start:chunk_start + BATCH_SIZE]
        
        batch_matchups = {}
        batch_player_stats = {} # Key: (player_name, format)
        batch_players = set()
        batch_teams = set()
        batch_matches = []
        
        # 1. Parse chunk
        for folder_path, filename in chunk_files:
            match_id_str = filename.replace(".yaml", "")
            try:
                match_id = int(match_id_str)
            except ValueError:
                continue
                
            filepath = os.path.join(folder_path, filename)
            info = parse_match_info(filepath)
            
            for t_name in [info["team_home"], info["team_away"]]:
                if t_name:
                    batch_teams.add(t_name)
                    
            players_teams = parse_match_players(filepath)
            all_players_in_match = {}
            for t_name, p_list in players_teams.items():
                for p_name in p_list:
                    all_players_in_match[p_name] = t_name
                    batch_players.add((p_name, t_name))
                    
            comp = info["competition"]
            mtype = info["match_type"]
            if comp and ("IPL" in comp or "Indian Premier League" in comp):
                fmt = "IPL"
            elif comp and ("BBL" in comp or "Big Bash League" in comp):
                fmt = "BBL"
            elif comp and ("CPL" in comp or "Caribbean Premier League" in comp):
                fmt = "CPL"
            elif comp and ("PSL" in comp or "Pakistan Super League" in comp):
                fmt = "PSL"
            elif mtype == "Test":
                fmt = "Test"
            elif mtype == "ODI":
                fmt = "ODI"
            elif mtype == "T20":
                fmt = "T20I" if "it20s" in filepath or "international" in str(info).lower() else "T20"
            else:
                fmt = "T20"
                
            deliveries = fast_parse_deliveries_full(filepath)
            
            match_stats = {}
            for p, t in all_players_in_match.items():
                match_stats[p] = {
                    "runs_scored": 0, "balls_faced": 0, "dismissed": False, "fours": 0, "sixes": 0, "dots": 0, "batted": False,
                    "runs_conceded": 0, "balls_bowled": 0, "wickets": 0, "bowled": False
                }
                
            for d in deliveries:
                batsman = d["batsman"]
                bowler = d["bowler"]
                
                key = (batsman, bowler)
                if key not in batch_matchups:
                    batch_matchups[key] = {
                        "runs": 0, "balls": 0, "dismissals": 0,
                        "caught": 0, "bowled": 0, "lbw": 0, "stumped": 0,
                        "fours": 0, "sixes": 0, "dots": 0
                    }
                m = batch_matchups[key]
                if d["wides"] == 0:
                    m["balls"] += 1
                m["runs"] += d["runs_batsman"]
                if d["runs_batsman"] == 0:
                    m["dots"] += 1
                elif d["runs_batsman"] == 4:
                    m["fours"] += 1
                elif d["runs_batsman"] == 6:
                    m["sixes"] += 1
                    
                if batsman in match_stats:
                    ms = match_stats[batsman]
                    ms["batted"] = True
                    ms["runs_scored"] += d["runs_batsman"]
                    if d["wides"] == 0:
                        ms["balls_faced"] += 1
                    if d["runs_batsman"] == 4:
                        ms["fours"] += 1
                    elif d["runs_batsman"] == 6:
                        ms["sixes"] += 1
                    elif d["runs_batsman"] == 0 and d["wides"] == 0 and d["noballs"] == 0:
                        ms["dots"] += 1
                        
                if d["wicket_kind"]:
                    p_out = d["player_out"]
                    wk = d["wicket_kind"]
                    
                    if wk not in ["run out", "retired hurt", "obstructing the field"]:
                        m["dismissals"] += 1
                        if wk == "caught":
                            m["caught"] += 1
                        elif wk == "bowled":
                            m["bowled"] += 1
                        elif wk == "lbw":
                            m["lbw"] += 1
                        elif wk == "stumped":
                            m["stumped"] += 1
                            
                    if p_out in match_stats:
                        match_stats[p_out]["dismissed"] = True
                        
                    if wk in ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']:
                        if bowler in match_stats:
                            match_stats[bowler]["wickets"] += 1
                            
                if bowler in match_stats:
                    ms = match_stats[bowler]
                    ms["bowled"] = True
                    ms["runs_conceded"] += (d["runs_batsman"] + d["wides"] + d["noballs"])
                    if d["wides"] == 0 and d["noballs"] == 0:
                        ms["balls_bowled"] += 1
                        
            for p, ms in match_stats.items():
                p_key = (p, fmt)
                if p_key not in batch_player_stats:
                    batch_player_stats[p_key] = {
                        "matches_played": 0, "innings_batted": 0, "runs_scored": 0,
                        "highest_score": 0, "dismissals_total": 0, "balls_faced_total": 0,
                        "centuries": 0, "half_centuries": 0, "wickets_taken": 0,
                        "runs_conceded_total": 0, "balls_bowled_total": 0,
                        "best_bowling_w": 0, "best_bowling_r": 999
                    }
                g = batch_player_stats[p_key]
                g["matches_played"] += 1
                if ms["batted"]:
                    g["innings_batted"] += 1
                    g["runs_scored"] += ms["runs_scored"]
                    g["balls_faced_total"] += ms["balls_faced"]
                    if ms["runs_scored"] > g["highest_score"]:
                        g["highest_score"] = ms["runs_scored"]
                    if ms["dismissed"]:
                        g["dismissals_total"] += 1
                    if ms["runs_scored"] >= 100:
                        g["centuries"] += 1
                    elif ms["runs_scored"] >= 50:
                        g["half_centuries"] += 1
                if ms["bowled"]:
                    g["wickets_taken"] += ms["wickets"]
                    g["runs_conceded_total"] += ms["runs_conceded"]
                    g["balls_bowled_total"] += ms["balls_bowled"]
                    if ms["wickets"] > g["best_bowling_w"] or (ms["wickets"] == g["best_bowling_w"] and ms["runs_conceded"] < g["best_bowling_r"]):
                        g["best_bowling_w"] = ms["wickets"]
                        g["best_bowling_r"] = ms["runs_conceded"]
                        
            match_date = None
            if info["date"]:
                try:
                    dt = datetime.strptime(info["date"], "%Y-%m-%d")
                    match_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    match_date = info["date"]
            else:
                match_date = datetime.now().strftime("%Y-%m-%d")
                
            batch_matches.append({
                "id": match_id,
                "match_type": info["match_type"],
                "team_home": info["team_home"],
                "team_away": info["team_away"],
                "result": info["result"],
                "match_date": match_date,
                "venue": info["venue"]
            })
            
        # 2. Write batch to DB in an atomic SQLAlchemy session transaction
        async with AsyncSessionLocal() as session:
            async with session.begin():
                
                # Check for skipped files & only process unique matches
                unique_batch_matches = []
                for m_info in batch_matches:
                    res = await session.execute(select(Match.id).where(Match.id == m_info["id"]))
                    exists = res.scalar()
                    if exists:
                        skipped_matches += 1
                    else:
                        unique_batch_matches.append(m_info)
                        
                if not unique_batch_matches:
                    # Nothing to insert, skip database updates for this batch
                    await session.commit()
                    progress_end = min(chunk_start + BATCH_SIZE, total_files)
                    print(f"Processed {progress_end}/{total_files} files (Skipped {skipped_matches} existing matches)...")
                    continue
                    
                # Sync Teams
                for t_name in batch_teams:
                    if t_name not in teams_db:
                        short_name = get_short_name(t_name)
                        new_team = Team(name=t_name, short_name=short_name, team_type="Franchise")
                        session.add(new_team)
                        await session.flush()
                        teams_db[t_name] = new_team.id
                        print(f"Created team: {t_name} ({short_name})")
                        
                # Sync Players
                for p_name, t_name in batch_players:
                    if p_name not in players_db:
                        new_player = Player(name=p_name, country=t_name)
                        session.add(new_player)
                        await session.flush()
                        players_db[p_name] = new_player.id
                        
                # Insert Matches
                for m_info in unique_batch_matches:
                    team_home_id = teams_db.get(m_info["team_home"])
                    team_away_id = teams_db.get(m_info["team_away"])
                    if not team_home_id or not team_away_id:
                        continue
                    new_match = Match(
                        id=m_info["id"],
                        match_type=m_info["match_type"],
                        team_home_id=team_home_id,
                        team_away_id=team_away_id,
                        status="Completed",
                        result=m_info["result"],
                        match_date=datetime.strptime(m_info["match_date"], "%Y-%m-%d").date(),
                        venue=m_info["venue"]
                    )
                    session.add(new_match)
                    loaded_matches += 1
                    
                # Sync Matchups (SQLAlchemy Dialect-Agnostic Bulk Fetch -> Merge -> Save)
                if batch_matchups:
                    batsmen = list({k[0] for k in batch_matchups.keys()})
                    bowlers = list({k[1] for k in batch_matchups.keys()})
                    
                    res = await session.execute(
                        select(MatchupCache).where(
                            MatchupCache.batsman_name.in_(batsmen),
                            MatchupCache.bowler_name.in_(bowlers)
                        )
                    )
                    existing_matchups = {}
                    for db_m in res.scalars().all():
                        key = (db_m.batsman_name, db_m.bowler_name)
                        existing_matchups[key] = db_m
                        
                    for key, m in batch_matchups.items():
                        batsman, bowler = key
                        if key in existing_matchups:
                            db_m = existing_matchups[key]
                            db_m.runs += m["runs"]
                            db_m.balls += m["balls"]
                            db_m.dismissals += m["dismissals"]
                            db_m.caught += m["caught"]
                            db_m.bowled += m["bowled"]
                            db_m.lbw += m["lbw"]
                            db_m.stumped += m["stumped"]
                            db_m.fours += m["fours"]
                            db_m.sixes += m["sixes"]
                            db_m.dots += m["dots"]
                        else:
                            new_m = MatchupCache(
                                batsman_name=batsman, bowler_name=bowler,
                                runs=m["runs"], balls=m["balls"], dismissals=m["dismissals"],
                                caught=m["caught"], bowled=m["bowled"], lbw=m["lbw"], stumped=m["stumped"],
                                fours=m["fours"], sixes=m["sixes"], dots=m["dots"]
                            )
                            session.add(new_m)
                            
                # Sync Player Stats (SQLAlchemy Dialect-Agnostic Bulk Fetch -> Merge -> Save)
                if batch_player_stats:
                    batch_player_ids = list({players_db[k[0]] for k in batch_player_stats.keys() if k[0] in players_db})
                    
                    existing_stats = {}
                    if batch_player_ids:
                        res = await session.execute(
                            select(PlayerStats).where(PlayerStats.player_id.in_(batch_player_ids))
                        )
                        for db_g in res.scalars().all():
                            existing_stats[(db_g.player_id, db_g.format)] = db_g
                            
                    for (p_name, fmt), ms in batch_player_stats.items():
                        pid = players_db.get(p_name)
                        if not pid:
                            continue
                            
                        key = (pid, fmt)
                        if key in existing_stats:
                            db_g = existing_stats[key]
                            runs_sc = db_g.runs_scored
                            avg = db_g.batting_average
                            sr = db_g.strike_rate
                            wkts = db_g.wickets_taken
                            bowl_avg = db_g.bowling_average
                            econ = db_g.economy_rate
                            
                            dismissals = int(round(runs_sc / avg)) if (avg and avg > 0) else 0
                            balls_faced = int(round((runs_sc / sr) * 100)) if (sr and sr > 0) else 0
                            runs_conceded = int(round(wkts * bowl_avg)) if (bowl_avg and bowl_avg > 0) else 0
                            balls_bowled = int(round((runs_conceded / econ) * 6)) if (econ and econ > 0) else 0
                            
                            matches_played = db_g.matches_played + ms["matches_played"]
                            innings_batted = db_g.innings_batted + ms["innings_batted"]
                            runs_scored = db_g.runs_scored + ms["runs_scored"]
                            highest_score = max(db_g.highest_score, ms["highest_score"])
                            dismissals_total = dismissals + ms["dismissals_total"]
                            balls_faced_total = balls_faced + ms["balls_faced_total"]
                            centuries = db_g.centuries + ms["centuries"]
                            half_centuries = db_g.half_centuries + ms["half_centuries"]
                            wickets_taken = db_g.wickets_taken + ms["wickets_taken"]
                            runs_conceded_total = runs_conceded + ms["runs_conceded_total"]
                            balls_bowled_total = balls_bowled + ms["balls_bowled_total"]
                            
                            current_best = db_g.best_bowling
                            cb_w, cb_r = 0, 999
                            if "/" in current_best:
                                try:
                                    cb_w = int(current_best.split("/")[0])
                                    cb_r = int(current_best.split("/")[1])
                                    
                                except Exception:
                                    pass
                            if ms["best_bowling_w"] > cb_w or (ms["best_bowling_w"] == cb_w and ms["best_bowling_r"] < cb_r):
                                best_bowling = f"{ms['best_bowling_w']}/{ms['best_bowling_r']}"
                            else:
                                best_bowling = current_best
                                
                            db_g.matches_played = matches_played
                            db_g.innings_batted = innings_batted
                            db_g.runs_scored = runs_scored
                            db_g.highest_score = highest_score
                            db_g.centuries = centuries
                            db_g.half_centuries = half_centuries
                            db_g.wickets_taken = wickets_taken
                            db_g.best_bowling = best_bowling
                            
                            db_g.batting_average = round(runs_scored / dismissals_total, 2) if dismissals_total > 0 else float(runs_scored)
                            db_g.strike_rate = round((runs_scored / balls_faced_total) * 100, 2) if balls_faced_total > 0 else 0.0
                            db_g.bowling_average = round(runs_conceded_total / wickets_taken, 2) if wickets_taken > 0 else 0.0
                            db_g.economy_rate = round((runs_conceded_total / balls_bowled_total) * 6, 2) if balls_bowled_total > 0 else 0.0
                        else:
                            new_g = PlayerStats(
                                player_id=pid, format=fmt,
                                matches_played=ms["matches_played"], innings_batted=ms["innings_batted"],
                                runs_scored=ms["runs_scored"], highest_score=ms["highest_score"],
                                batting_average=round(ms["runs_scored"] / ms["dismissals_total"], 2) if ms["dismissals_total"] > 0 else float(ms["runs_scored"]),
                                strike_rate=round((ms["runs_scored"] / ms["balls_faced_total"]) * 100, 2) if ms["balls_faced_total"] > 0 else 0.0,
                                centuries=ms["centuries"], half_centuries=ms["half_centuries"],
                                wickets_taken=ms["wickets_taken"],
                                bowling_average=round(ms["runs_conceded_total"] / ms["wickets_taken"], 2) if ms["wickets_taken"] > 0 else 0.0,
                                economy_rate=round((ms["runs_conceded_total"] / ms["balls_bowled_total"]) * 6, 2) if ms["balls_bowled_total"] > 0 else 0.0,
                                best_bowling=f"{ms['best_bowling_w']}/{ms['best_bowling_r']}"
                            )
                            session.add(new_g)
                            
                # Commits automatically on block exit
                
        progress_end = min(chunk_start + BATCH_SIZE, total_files)
        print(f"Processed {progress_end}/{total_files} files (Skipped {skipped_matches} existing matches)...")
        
    print("==================================================")
    print(f"SQLAlchemy ETL completed in {time.time() - t0:.2f}s!")
    print(f"Loaded {loaded_matches} new matches into the database.")
    print(f"Skipped {skipped_matches} already indexed matches.")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
