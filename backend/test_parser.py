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

if __name__ == "__main__":
    filepath = r"C:\Users\HP\.gemini\antigravity\scratch\cricketgpt\Archive\criket-data\ipl\1082591.yaml"
    res = parse_match_players(filepath)
    print("Parsed Players:")
    for team, players_list in res.items():
        print(f"Team: {team}")
        for p in players_list:
            print(f"  - {p}")
