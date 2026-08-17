import os

class CricketDataLoader:
    def __init__(self, data_dir=None):
        if data_dir is None:
            # Resolve relative path from backend/cricket_data.py
            PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(PROJECT_ROOT, "Archive", "criket-data")
        else:
            self.data_dir = data_dir
            
    def get_match_filepath(self, match_id):
        folders = ["ipl", "tests", "odis", "t20s"]
        for folder in folders:
            filepath = os.path.join(self.data_dir, folder, f"{match_id}.yaml")
            if os.path.exists(filepath):
                return filepath
        return os.path.join(self.data_dir, "ipl", f"{match_id}.yaml")
        
    def list_match_ids(self):
        folders = ["ipl", "tests", "odis", "t20s"]
        match_ids = []
        for folder in folders:
            folder_path = os.path.join(self.data_dir, folder)
            if os.path.exists(folder_path):
                match_ids.extend([int(f.replace(".yaml", "")) for f in os.listdir(folder_path) if f.endswith(".yaml") and f.replace(".yaml", "").isdigit()])
        return match_ids
        
    def load_match_info(self, match_id):
        """Loads match metadata info block."""
        filepath = self.get_match_filepath(match_id)
        if not os.path.exists(filepath):
            return None
            
        info = {
            "id": match_id,
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

    def load_match_deliveries(self, match_id):
        """Loads and parses all ball-by-ball deliveries for a match."""
        filepath = self.get_match_filepath(match_id)
        if not os.path.exists(filepath):
            return []
            
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

# Singleton Instance
cricket_data = CricketDataLoader()
