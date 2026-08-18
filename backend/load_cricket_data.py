import os
import sqlite3
import time
from datetime import datetime

# Path Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(PROJECT_ROOT, "Archive", "criket-data")
DB_PATH = os.path.join(PROJECT_ROOT, "backend", "cricketgpt.db")

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

def main():
    print("==================================================")
    print("  CricketGPT True Incremental Batch-ETL Loader   ")
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
    
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH, timeout=30.0, isolation_level=None)
    cursor = conn.cursor()
    
    # Ensure indices and unique constraints exist to support upserts
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_matchup_unique ON matchup_cache (batsman_name, bowler_name)")
    
    # Setup players tables if not exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        country TEXT NOT NULL,
        batting_style TEXT,
        bowling_style TEXT,
        image_url TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        format TEXT NOT NULL,
        matches_played INTEGER DEFAULT 0,
        innings_batted INTEGER DEFAULT 0,
        runs_scored INTEGER DEFAULT 0,
        highest_score INTEGER DEFAULT 0,
        batting_average REAL DEFAULT 0.0,
        strike_rate REAL DEFAULT 0.0,
        centuries INTEGER DEFAULT 0,
        half_centuries INTEGER DEFAULT 0,
        wickets_taken INTEGER DEFAULT 0,
        bowling_average REAL DEFAULT 0.0,
        economy_rate REAL DEFAULT 0.0,
        best_bowling TEXT DEFAULT '0/0',
        FOREIGN KEY (player_id) REFERENCES players (id),
        UNIQUE (player_id, format)
    )
    """)
    
    # Clean up duplicate player stats before creating unique index
    cursor.execute("""
    DELETE FROM player_stats 
    WHERE id NOT IN (
        SELECT MIN(id) 
        FROM player_stats 
        GROUP BY player_id, format
    )
    """)
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_player_stats_unique ON player_stats (player_id, format)")
    
    # Get existing maps
    cursor.execute("SELECT id, name FROM teams")
    teams_db = {name: tid for tid, name in cursor.fetchall()}
    
    cursor.execute("SELECT id, name FROM players")
    players_db = {name: pid for pid, name in cursor.fetchall()}
    
    t0 = time.time()
    loaded_matches = 0
    skipped_matches = 0
    
    BATCH_SIZE = 500
    total_files = len(files)
    
    for chunk_start in range(0, total_files, BATCH_SIZE):
        chunk_files = files[chunk_start:chunk_start + BATCH_SIZE]
        
        # Start transaction for current batch
        conn.execute("BEGIN IMMEDIATE")
        
        batch_matchups = {}
        batch_player_stats = {} # Key: (player_name, format)
        batch_players = set()
        batch_teams = set()
        batch_matches_inserted = 0
        
        # 1. Parse and compile the current batch in memory
        for folder_path, filename in chunk_files:
            match_id_str = filename.replace(".yaml", "")
            try:
                match_id = int(match_id_str)
            except ValueError:
                continue
                
            # Check if match already exists
            cursor.execute("SELECT id FROM matches WHERE id = ?", (match_id,))
            exists = cursor.fetchone()
            if exists:
                skipped_matches += 1
                continue
                
            filepath = os.path.join(folder_path, filename)
            info = parse_match_info(filepath)
            
            # Record teams
            for t_name in [info["team_home"], info["team_away"]]:
                if t_name:
                    batch_teams.add(t_name)
                    
            # Parse players
            players_teams = parse_match_players(filepath)
            all_players_in_match = {}
            for t_name, p_list in players_teams.items():
                for p_name in p_list:
                    all_players_in_match[p_name] = t_name
                    batch_players.add((p_name, t_name))
                    
            # Resolve match format
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
                
            # Parse deliveries
            deliveries = fast_parse_deliveries_full(filepath)
            
            # Aggregate stats for this match
            match_stats = {}
            for p, t in all_players_in_match.items():
                match_stats[p] = {
                    "runs_scored": 0, "balls_faced": 0, "dismissed": False, "fours": 0, "sixes": 0, "dots": 0, "batted": False,
                    "runs_conceded": 0, "balls_bowled": 0, "wickets": 0, "bowled": False
                }
                
            for d in deliveries:
                batsman = d["batsman"]
                bowler = d["bowler"]
                
                # Matchups
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
                    
                # Batting
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
                        
                # Wickets
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
                            
                # Bowling
                if bowler in match_stats:
                    ms = match_stats[bowler]
                    ms["bowled"] = True
                    ms["runs_conceded"] += (d["runs_batsman"] + d["wides"] + d["noballs"])
                    if d["wides"] == 0 and d["noballs"] == 0:
                        ms["balls_bowled"] += 1
                        
            # Merge match player stats into batch player stats
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
                        
            # Load match record
            match_date = None
            if info["date"]:
                try:
                    dt = datetime.strptime(info["date"], "%Y-%m-%d")
                    match_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    match_date = info["date"]
            else:
                match_date = datetime.now().strftime("%Y-%m-%d")
                
            # Get team IDs for insert (done below once teams are created in DB)
            info["match_date"] = match_date
            info["match_id"] = match_id
            chunk_files_meta = chunk_files  # helper reference
            
            # We defer actual insertion to step 2 once teams/players are resolved in DB
            
        # 2. Sync Teams in database
        for t_name in batch_teams:
            if t_name not in teams_db:
                short_name = get_short_name(t_name)
                cursor.execute(
                    "INSERT INTO teams (name, short_name, team_type) VALUES (?, ?, 'Franchise')",
                    (t_name, short_name)
                )
                teams_db[t_name] = cursor.lastrowid
                print(f"Created team: {t_name} ({short_name})")
                
        # 3. Sync Players in database
        for p_name, t_name in batch_players:
            if p_name not in players_db:
                cursor.execute("INSERT OR IGNORE INTO players (name, country) VALUES (?, ?)", (p_name, t_name))
                cursor.execute("SELECT id FROM players WHERE name = ?", (p_name,))
                row = cursor.fetchone()
                if row:
                    players_db[p_name] = row[0]
                else:
                    players_db[p_name] = cursor.lastrowid
                    
        # 4. Insert Match records
        for folder_path, filename in chunk_files:
            match_id_str = filename.replace(".yaml", "")
            try:
                match_id = int(match_id_str)
            except ValueError:
                continue
                
            # If it already existed in DB, it was skipped earlier
            filepath = os.path.join(folder_path, filename)
            info = parse_match_info(filepath)
            team_home_id = teams_db.get(info["team_home"])
            team_away_id = teams_db.get(info["team_away"])
            
            if not team_home_id or not team_away_id:
                continue
                
            cursor.execute("SELECT id FROM matches WHERE id = ?", (match_id,))
            if not cursor.fetchone():
                match_date = None
                if info["date"]:
                    try:
                        dt = datetime.strptime(info["date"], "%Y-%m-%d")
                        match_date = dt.strftime("%Y-%m-%d")
                    except Exception:
                        match_date = info["date"]
                else:
                    match_date = datetime.now().strftime("%Y-%m-%d")
                    
                cursor.execute(
                    "INSERT INTO matches (id, match_type, team_home_id, team_away_id, status, result, match_date, venue) VALUES (?, ?, ?, ?, 'Completed', ?, ?, ?)",
                    (match_id, info["match_type"], team_home_id, team_away_id, info["result"], match_date, info["venue"])
                )
                loaded_matches += 1
                
        # 5. Save Matchups (SQLite Upsert)
        if batch_matchups:
            insert_matchups = []
            for (batsman, bowler), m in batch_matchups.items():
                insert_matchups.append((
                    batsman, bowler, m["runs"], m["balls"], m["dismissals"],
                    m["caught"], m["bowled"], m["lbw"], m["stumped"],
                    m["fours"], m["sixes"], m["dots"]
                ))
            cursor.executemany("""
            INSERT INTO matchup_cache (
                batsman_name, bowler_name, runs, balls, dismissals,
                caught, bowled, lbw, stumped, fours, sixes, dots
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(batsman_name, bowler_name) DO UPDATE SET
                runs = runs + excluded.runs,
                balls = balls + excluded.balls,
                dismissals = dismissals + excluded.dismissals,
                caught = caught + excluded.caught,
                bowled = bowled + excluded.bowled,
                lbw = lbw + excluded.lbw,
                stumped = stumped + excluded.stumped,
                fours = fours + excluded.fours,
                sixes = sixes + excluded.sixes,
                dots = dots + excluded.dots
            """, insert_matchups)
            
        # 6. Save Player Stats (Batch Fetch -> Merge -> Upsert)
        if batch_player_stats:
            batch_player_ids = set()
            for (p_name, fmt) in batch_player_stats.keys():
                pid = players_db.get(p_name)
                if pid:
                    batch_player_ids.add(pid)
                    
            existing_stats = {}
            if batch_player_ids:
                placeholders = ",".join("?" for _ in batch_player_ids)
                cursor.execute(f"""
                    SELECT player_id, format, matches_played, innings_batted, runs_scored, 
                           highest_score, batting_average, strike_rate, centuries, half_centuries, 
                           wickets_taken, bowling_average, economy_rate, best_bowling
                    FROM player_stats
                    WHERE player_id IN ({placeholders})
                """, list(batch_player_ids))
                for row in cursor.fetchall():
                    pid, fmt = row[0], row[1]
                    runs_sc = row[4]
                    avg = row[6]
                    sr = row[7]
                    wkts = row[10]
                    bowl_avg = row[11]
                    econ = row[12]
                    
                    dismissals = int(round(runs_sc / avg)) if (avg and avg > 0) else 0
                    balls_faced = int(round((runs_sc / sr) * 100)) if (sr and sr > 0) else 0
                    runs_conceded = int(round(wkts * bowl_avg)) if (bowl_avg and bowl_avg > 0) else 0
                    balls_bowled = int(round((runs_conceded / econ) * 6)) if (econ and econ > 0) else 0
                    
                    existing_stats[(pid, fmt)] = {
                        "matches_played": row[2],
                        "innings_batted": row[3],
                        "runs_scored": runs_sc,
                        "highest_score": row[5],
                        "batting_average": avg,
                        "strike_rate": sr,
                        "centuries": row[8],
                        "half_centuries": row[9],
                        "wickets_taken": wkts,
                        "bowling_average": bowl_avg,
                        "economy_rate": econ,
                        "best_bowling": row[13],
                        "dismissals_total": dismissals,
                        "balls_faced_total": balls_faced,
                        "runs_conceded_total": runs_conceded,
                        "balls_bowled_total": balls_bowled
                    }
                    
            insert_stats = []
            for (p_name, fmt), ms in batch_player_stats.items():
                pid = players_db.get(p_name)
                if not pid:
                    continue
                    
                key = (pid, fmt)
                g = existing_stats.get(key, {
                    "matches_played": 0, "innings_batted": 0, "runs_scored": 0,
                    "highest_score": 0, "batting_average": 0.0, "strike_rate": 0.0,
                    "centuries": 0, "half_centuries": 0, "wickets_taken": 0,
                    "bowling_average": 0.0, "economy_rate": 0.0, "best_bowling": "0/0",
                    "dismissals_total": 0, "balls_faced_total": 0,
                    "runs_conceded_total": 0, "balls_bowled_total": 0
                })
                
                g["matches_played"] += ms["matches_played"]
                if ms["innings_batted"] > 0:
                    g["innings_batted"] += ms["innings_batted"]
                    g["runs_scored"] += ms["runs_scored"]
                    g["balls_faced_total"] += ms["balls_faced_total"]
                    if ms["highest_score"] > g["highest_score"]:
                        g["highest_score"] = ms["highest_score"]
                    g["dismissals_total"] += ms["dismissals_total"]
                    g["centuries"] += ms["centuries"]
                    g["half_centuries"] += ms["half_centuries"]
                    
                if ms["balls_bowled_total"] > 0:
                    g["wickets_taken"] += ms["wickets_taken"]
                    g["runs_conceded_total"] += ms["runs_conceded_total"]
                    g["balls_bowled_total"] += ms["balls_bowled_total"]
                    
                    current_best = g["best_bowling"]
                    cb_w, cb_r = 0, 999
                    if "/" in current_best:
                        try:
                            cb_w = int(current_best.split("/")[0])
                            cb_r = int(current_best.split("/")[1])
                        except Exception:
                            pass
                    if ms["best_bowling_w"] > cb_w or (ms["best_bowling_w"] == cb_w and ms["best_bowling_r"] < cb_r):
                        g["best_bowling"] = f"{ms['best_bowling_w']}/{ms['best_bowling_r']}"
                        
                # Averages recalculation
                if g["dismissals_total"] > 0:
                    g["batting_average"] = round(g["runs_scored"] / g["dismissals_total"], 2)
                else:
                    g["batting_average"] = float(g["runs_scored"])
                    
                if g["balls_faced_total"] > 0:
                    g["strike_rate"] = round((g["runs_scored"] / g["balls_faced_total"]) * 100, 2)
                else:
                    g["strike_rate"] = 0.0
                    
                if g["wickets_taken"] > 0:
                    g["bowling_average"] = round(g["runs_conceded_total"] / g["wickets_taken"], 2)
                else:
                    g["bowling_average"] = 0.0
                    
                if g["balls_bowled_total"] > 0:
                    g["economy_rate"] = round((g["runs_conceded_total"] / g["balls_bowled_total"]) * 6, 2)
                else:
                    g["economy_rate"] = 0.0
                    
                insert_stats.append((
                    pid, fmt, g["matches_played"], g["innings_batted"], g["runs_scored"],
                    g["highest_score"], g["batting_average"], g["strike_rate"], g["centuries"],
                    g["half_centuries"], g["wickets_taken"], g["bowling_average"], g["economy_rate"],
                    g["best_bowling"]
                ))
                
            cursor.executemany("""
            INSERT INTO player_stats (
                player_id, format, matches_played, innings_batted, runs_scored,
                highest_score, batting_average, strike_rate, centuries,
                half_centuries, wickets_taken, bowling_average, economy_rate,
                best_bowling
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id, format) DO UPDATE SET
                matches_played = excluded.matches_played,
                innings_batted = excluded.innings_batted,
                runs_scored = excluded.runs_scored,
                highest_score = excluded.highest_score,
                batting_average = excluded.batting_average,
                strike_rate = excluded.strike_rate,
                centuries = excluded.centuries,
                half_centuries = excluded.half_centuries,
                wickets_taken = excluded.wickets_taken,
                bowling_average = excluded.bowling_average,
                economy_rate = excluded.economy_rate,
                best_bowling = excluded.best_bowling
            """, insert_stats)
            
        # Commit the transaction for the current batch
        conn.execute("COMMIT")
        
        progress_end = min(chunk_start + BATCH_SIZE, total_files)
        print(f"Processed {progress_end}/{total_files} files (Skipped {skipped_matches} existing matches)...")
        
    conn.close()
    
    print("==================================================")
    print(f"Incremental ETL completed in {time.time() - t0:.2f}s!")
    print(f"Loaded {loaded_matches} new matches into the database.")
    print(f"Skipped {skipped_matches} already indexed matches.")
    print("==================================================")

if __name__ == "__main__":
    main()
