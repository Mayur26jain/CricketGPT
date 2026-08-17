import sys
from app.services.external_apis import ExternalAPIService

def verify():
    print("Executing dynamic search & matchup verification tests...")
    
    # 1. Test Rohit search mapping
    rohit_stats = ExternalAPIService.search_and_import_player("rohit")
    print(f"Search 'rohit' -> Country: {rohit_stats.get('country')}, Name: {rohit_stats.get('name')}")
    assert rohit_stats.get('country') == "India", "Failed to map Rohit to India!"
    
    # 2. Test Maxwell search mapping (heuristics classifier)
    maxwell_stats = ExternalAPIService.search_and_import_player("Glenn Maxwell")
    print(f"Search 'Glenn Maxwell' -> Country: {maxwell_stats.get('country')}, Name: {maxwell_stats.get('name')}")
    assert maxwell_stats.get('country') == "Australia", "Failed to map Maxwell to Australia!"
    
    # 3. Test Babar search mapping (heuristics classifier)
    babar_stats = ExternalAPIService.search_and_import_player("Babar Azam")
    print(f"Search 'Babar Azam' -> Country: {babar_stats.get('country')}, Name: {babar_stats.get('name')}")
    assert babar_stats.get('country') == "Pakistan", "Failed to map Babar to Pakistan!"
    
    # 4. Test Matchup Stats Generator
    matchup = ExternalAPIService.generate_matchup_stats("Glenn Maxwell", "Jasprit Bumrah")
    print(f"Matchup 'Glenn Maxwell vs Jasprit Bumrah' -> Runs: {matchup.get('runs')}, Dismissals: {matchup.get('dismissals')}")
    assert matchup.get('runs') > 0, "Matchup runs should be greater than zero!"
    
    print("\nAll verification checkpoints successfully passed!")

if __name__ == "__main__":
    verify()
