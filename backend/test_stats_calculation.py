import os

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

def parse_deliveries_full(filepath):
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
                sub_line = lines[i].strip()
                if sub_line.startswith("batsman:"):
                    val = sub_line.split(":", 1)[1].strip()
                    batsman = val.strip("'\"")
                elif sub_line.startswith("bowler:"):
                    val = sub_line.split(":", 1)[1].strip()
                    bowler = val.strip("'\"")
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

def calculate_stats(filepath):
    players_teams = parse_match_players(filepath)
    all_players = set()
    for team, p_list in players_teams.items():
        all_players.update(p_list)
        
    deliveries = parse_deliveries_full(filepath)
    
    batting_stats = {}
    bowling_stats = {}
    
    # Initialize stats for all players participating in the match
    for p in all_players:
        batting_stats[p] = {"runs": 0, "balls": 0, "dismissed": False, "fours": 0, "sixes": 0, "dots": 0, "batted": False}
        bowling_stats[p] = {"runs_conceded": 0, "balls": 0, "wickets": 0, "bowled": False}
        
    for d in deliveries:
        batsman = d["batsman"]
        bowler = d["bowler"]
        
        # Batting
        if batsman in batting_stats:
            batting_stats[batsman]["batted"] = True
            batting_stats[batsman]["runs"] += d["runs_batsman"]
            if d["wides"] == 0:
                batting_stats[batsman]["balls"] += 1
            if d["runs_batsman"] == 4:
                batting_stats[batsman]["fours"] += 1
            elif d["runs_batsman"] == 6:
                batting_stats[batsman]["sixes"] += 1
            elif d["runs_batsman"] == 0 and d["wides"] == 0 and d["noballs"] == 0:
                batting_stats[batsman]["dots"] += 1
                
        # Wicket checking
        if d["wicket_kind"]:
            p_out = d["player_out"]
            if p_out in batting_stats:
                batting_stats[p_out]["dismissed"] = True
            if d["wicket_kind"] in ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']:
                if bowler in bowling_stats:
                    bowling_stats[bowler]["wickets"] += 1
                    
        # Bowling
        if bowler in bowling_stats:
            bowling_stats[bowler]["bowled"] = True
            bowling_stats[bowler]["runs_conceded"] += (d["runs_batsman"] + d["wides"] + d["noballs"])
            if d["wides"] == 0 and d["noballs"] == 0:
                bowling_stats[bowler]["balls"] += 1
                
    return batting_stats, bowling_stats

if __name__ == "__main__":
    filepath = r"C:\Users\HP\.gemini\antigravity\scratch\cricketgpt\Archive\criket-data\ipl\1082591.yaml"
    bat, bowl = calculate_stats(filepath)
    print("BATTING STATS:")
    for p, s in sorted(bat.items(), key=lambda x: x[1]["runs"], reverse=True):
        if s["batted"]:
            status = "out" if s["dismissed"] else "not out"
            print(f"  {p}: {s['runs']} runs ({s['balls']} balls, {s['fours']}x4, {s['sixes']}x6, {status})")
            
    print("\nBOWLING STATS:")
    for p, s in sorted(bowl.items(), key=lambda x: x[1]["wickets"], reverse=True):
        if s["bowled"]:
            overs = f"{s['balls'] // 6}.{s['balls'] % 6}"
            print(f"  {p}: {s['wickets']} wkts for {s['runs_conceded']} runs ({overs} overs)")
