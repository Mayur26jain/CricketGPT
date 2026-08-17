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
        "competition": "IPL",
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

def fast_parse_deliveries(filepath):
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
            runs = 0
            is_wide = False
            wicket_kind = ""
            
            i += 1
            while i < n and not lines[i].startswith("    - ") and not lines[i].startswith("  - ") and not lines[i].startswith("info:") and not lines[i].startswith("meta:"):
                sub_line = lines[i].strip()
                if sub_line.startswith("batsman:"):
                    val = sub_line.split(":", 1)[1].strip()
                    try:
                        int(val)
                    except ValueError:
                        batsman = val
                elif sub_line.startswith("bowler:"):
                    bowler = sub_line.split(":", 1)[1].strip()
                elif sub_line.startswith("wides:"):
                    is_wide = True
                elif sub_line.startswith("wicket:"):
                    j = i + 1
                    while j < n and lines[j].startswith("        "):
                        if lines[j].strip().startswith("kind:"):
                            wicket_kind = lines[j].strip().split(":", 1)[1].strip()
                            break
                        j += 1
                elif sub_line.startswith("runs:"):
                    j = i + 1
                    while j < n and lines[j].startswith("        "):
                        if lines[j].strip().startswith("batsman:"):
                            try:
                                runs = int(lines[j].strip().split(":", 1)[1].strip())
                            except Exception:
                                pass
                            break
                        j += 1
                i += 1
            if batsman and bowler:
                deliveries.append({
                    "batsman": batsman,
                    "bowler": bowler,
                    "runs": runs,
                    "is_wide": is_wide,
                    "wicket_kind": wicket_kind
                })
        else:
            i += 1
    return deliveries

def main():
    print("==================================================")
    print("   CricketGPT IPL Data Loader & Matchup Indexer   ")
    print("==================================================")
    
    if not os.path.exists(DATASET_DIR):
        print(f"Error: IPL dataset directory not found at: {DATASET_DIR}")
        return
        
    print(f"Scanning match files from subfolders in: {DATASET_DIR}")
    folders = ["ipl", "tests", "odis", "t20s"]
    files = []
    for folder in folders:
        folder_path = os.path.join(DATASET_DIR, folder)
        if os.path.exists(folder_path):
            files.extend([(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".yaml")])
    print(f"Found {len(files)} match files across {', '.join(folders)}.")
    
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create table matchup_cache if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matchup_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batsman_name TEXT NOT NULL,
        bowler_name TEXT NOT NULL,
        runs INTEGER DEFAULT 0,
        balls INTEGER DEFAULT 0,
        dismissals INTEGER DEFAULT 0,
        caught INTEGER DEFAULT 0,
        bowled INTEGER DEFAULT 0,
        lbw INTEGER DEFAULT 0,
        stumped INTEGER DEFAULT 0,
        fours INTEGER DEFAULT 0,
        sixes INTEGER DEFAULT 0,
        dots INTEGER DEFAULT 0
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_matchup_names ON matchup_cache (batsman_name, bowler_name)")
    
    t0 = time.time()
    loaded_matches = 0
    matchups = {}
    
    # Get existing teams mapping to avoid duplicate queries/insertions
    cursor.execute("SELECT id, name FROM teams")
    teams_db = {name: tid for tid, name in cursor.fetchall()}
    
    for index, (folder_path, filename) in enumerate(files):
        filepath = os.path.join(folder_path, filename)
        match_id_str = filename.replace(".yaml", "")
        try:
            match_id = int(match_id_str)
        except ValueError:
            continue
            
        info = parse_match_info(filepath)
        
        # Load Teams
        team_ids = []
        for team_name in [info["team_home"], info["team_away"]]:
            if not team_name:
                continue
            if team_name not in teams_db:
                short_name = get_short_name(team_name)
                cursor.execute(
                    "INSERT INTO teams (name, short_name, team_type) VALUES (?, ?, 'Franchise')",
                    (team_name, short_name)
                )
                tid = cursor.lastrowid
                teams_db[team_name] = tid
                print(f"Created team: {team_name} ({short_name})")
            team_ids.append(teams_db[team_name])
            
        if len(team_ids) < 2:
            continue
            
        # Parse and clean Date
        match_date = None
        if info["date"]:
            try:
                # Format to standard YYYY-MM-DD
                dt = datetime.strptime(info["date"], "%Y-%m-%d")
                match_date = dt.strftime("%Y-%m-%d")
            except Exception:
                match_date = info["date"]
        else:
            match_date = datetime.now().strftime("%Y-%m-%d")
            
        # Check if match already exists
        cursor.execute("SELECT id FROM matches WHERE id = ?", (match_id,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(
                "INSERT INTO matches (id, match_type, team_home_id, team_away_id, status, result, match_date, venue) VALUES (?, ?, ?, ?, 'Completed', ?, ?, ?)",
                (match_id, info["match_type"], team_ids[0], team_ids[1], info["result"], match_date, info["venue"])
            )
            loaded_matches += 1
            
        # Parse ball-by-ball deliveries for matchup index
        deliveries = fast_parse_deliveries(filepath)
        for d in deliveries:
            batsman_name = d["batsman"].strip()
            bowler_name = d["bowler"].strip()
            if not batsman_name or not bowler_name:
                continue
                
            key = (batsman_name, bowler_name)
            if key not in matchups:
                matchups[key] = {
                    "runs": 0, "balls": 0, "dismissals": 0,
                    "caught": 0, "bowled": 0, "lbw": 0, "stumped": 0,
                    "fours": 0, "sixes": 0, "dots": 0
                }
            
            m = matchups[key]
            if not d["is_wide"]:
                m["balls"] += 1
            m["runs"] += d["runs"]
            if d["runs"] == 0:
                m["dots"] += 1
            elif d["runs"] == 4:
                m["fours"] += 1
            elif d["runs"] == 6:
                m["sixes"] += 1
                
            wk = d["wicket_kind"]
            if wk and wk not in ["run out", "retired hurt", "obstructing the field"]:
                m["dismissals"] += 1
                if wk == "caught":
                    m["caught"] += 1
                elif wk == "bowled":
                    m["bowled"] += 1
                elif wk == "lbw":
                    m["lbw"] += 1
                elif wk == "stumped":
                    m["stumped"] += 1
                    
        if (index + 1) % 100 == 0 or (index + 1) == len(files):
            print(f"Processed {index + 1}/{len(files)} match files...")
            
    # Load all matchups into matchup_cache table
    print("Writing matchups cache to database...")
    cursor.execute("DELETE FROM matchup_cache")
    
    insert_data = []
    for (batsman, bowler), m in matchups.items():
        insert_data.append((
            batsman, bowler, m["runs"], m["balls"], m["dismissals"],
            m["caught"], m["bowled"], m["lbw"], m["stumped"],
            m["fours"], m["sixes"], m["dots"]
        ))
        
    cursor.executemany("""
    INSERT INTO matchup_cache (
        batsman_name, bowler_name, runs, balls, dismissals,
        caught, bowled, lbw, stumped, fours, sixes, dots
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insert_data)
    
    conn.commit()
    conn.close()
    
    print("==================================================")
    print(f"Successfully loaded {loaded_matches} new IPL matches into the database.")
    print(f"Successfully indexed {len(matchups)} unique batsman-vs-bowler matchups.")
    print(f"ETL pipeline completed in {time.time() - t0:.2f}s!")
    print("==================================================")

if __name__ == "__main__":
    main()
