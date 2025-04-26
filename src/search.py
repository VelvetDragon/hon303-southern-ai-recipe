import json
import re
from pathlib import Path
from rapidfuzz import process, fuzz

DATA_PATH = Path(__file__).parent.parent / "data" / "processed" / "recipes_clean.jsonl"

def parse_recipe(text: str) -> dict:
    title_match = re.search(r"TITLE:\s*\*\*(.*?)\*\*", text, re.S)
    ingr_match  = re.search(r"<\|ingredients\|>(.*?)<\|steps\|>", text, re.S)
    steps_match = re.search(r"<\|steps\|>(.*?)<\|endofrecipe\|>", text, re.S)

    title = title_match.group(1).strip() if title_match else "Untitled"
    ingr_block = ingr_match.group(1).strip()   if ingr_match  else ""
    steps_block= steps_match.group(1).strip()  if steps_match else ""

    ingredients = [line.strip("- ").strip()
                   for line in ingr_block.splitlines() if line.strip()]
    steps       = [line.strip()
                   for line in steps_block.splitlines() if line.strip()]

    return {"title": title, "ingredients": ingredients, "steps": steps}

# --- Load & parse all recipes ---
_raw = []
with open(DATA_PATH, "r", encoding="utf-8") as f:
    for line in f:
        data = json.loads(line)
        _raw.append(data["text"])

recipes = [parse_recipe(t) for t in _raw]

# --- Build lowercase search keys ---
# Combine title + ingredients, then lowercase
search_keys = [
    (r["title"] + " " + " ".join(r["ingredients"])).lower()
    for r in recipes
]

def search_local(query: str, limit: int = 5, score_cutoff: int = 50):
    """
    Fuzzy‐search over title+ingredients (all lowercase) using token_set_ratio.
    Returns up to `limit` recipes with score ≥ score_cutoff.
    """
    q = query.lower()
    # process.extract returns (matched_key, score, idx)
    results = process.extract(
        q,
        search_keys,
        scorer=fuzz.token_set_ratio,
        limit=limit
    )
    matches = [
        (recipes[idx], score)
        for _, score, idx in results
        if score >= score_cutoff
    ]
    return matches
