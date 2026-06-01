import json
import sys
sys.path.insert(0, '.')
from src.services import fallback_triage

with open('src/data/billets_test.json', encoding='utf-8') as f:
    tickets = json.load(f)

results = [(t['id'], t['categorie_attendue'], t['priorite_attendue'], fallback_triage(t['description'], None)) for t in tickets]

for r in results:
    print(f"{r[0]}: Expected {r[1]}|{r[2]} -> Got {r[3]['categorie']}|{r[3]['priorite']}")

successes = sum(1 for r in results if r[1] == r[3]['categorie'] and r[2] == r[3]['priorite'])
print(f"Success: {successes/len(results)*100}%")
