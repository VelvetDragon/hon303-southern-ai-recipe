# src/data_preprocessing/clean_ocr.py

import re, json, pathlib

RAW_DIR  = pathlib.Path("data/raw/cookbooks")
OUT_PATH = pathlib.Path("data/processed/recipes_clean.jsonl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

SEP_RE       = re.compile(r"^\s*-{3,}\s*$", flags=re.M)
# 1) Define your OCR‐artifact normalizer first:
REPLACEMENTS = {
    "\u201c": '"', "\u201d": '"',
    "\u2018": "'", "\u2019": "'",
    "\u2013": "-",  "\u2014": "-",
    "\xa0": " ",   "\f": " ",
}

def normalize(text: str) -> str:
    """Normalize text by replacing special characters and collapsing whitespace."""
    text = SEP_RE.sub("", text)
    for bad, good in REPLACEMENTS.items():
        text = text.replace(bad, good)
    text = re.sub(r"[ \t]{2,}", " ", text)      # collapse spaces
    text = re.sub(r"\n{3,}", "\n\n", text)      # collapse blank lines
    # Remove page numbers
    text = re.sub(r"\n?\s*Page\s+\d+\s*\n?", "\n", text, flags=re.I)
    return text.strip()


def is_recipe_title(line: str) -> bool:
    """Identify recipe titles based on Southern cookbook patterns."""
    line = line.strip()
    
    # Skip empty lines or single words (like "INDEX")
    if not line or len(line.split()) <= 1:
        return False
    
    # Skip lines that look like measurements or ingredient quantities
    if re.match(r"^\d+\s+", line) or re.match(r"^[0-9½¼⅓⅔]+\s+[cCTtgk]\.?\s+", line):
        return False
    
    # Skip lines that look like ingredient lists
    if re.search(r"\b(cup|can|package|recipe|sauce|oz|pound|tablespoon|teaspoon|tbsp|tsp)\b", 
                 line, re.IGNORECASE):
        return False
    
    # Skip instruction lines
    instruction_starters = ["mix", "combine", "stir", "add", "pour", "cook", "bake", "heat", 
                           "place", "arrange", "season", "serve", "preheat", "drain"]
    for starter in instruction_starters:
        if line.lower().startswith(starter):
            return False
    
    # All CAPS titles (common in community cookbooks)
    if line.isupper() and len(line) <= 60:
        return True
    
    # Title Case with 2-6 words (common recipe title format)
    words = line.split()
    if 1 < len(words) <= 6 and all(w[:1].isupper() for w in words if len(w) > 1):
        # Further verification - avoid instruction lines in Title Case
        if not re.search(r"\.\s*$", line):  # Titles rarely end with periods
            return True
            
    return False

def parse_sections(title: str, lines: list[str]) -> dict | None:
    """
    From the raw lines after a title, extract:
      - ingredients: list of strings (no '- ' prefix)
      - steps: list of strings (no numbering)
    """
    ing, steps = [], []
    section = None

    for line in lines:
        line = line.strip()

        # Detect section headers (Markdown-style **...** or plain text)
        if re.match(r"(\*\*)?ingredients:(\*\*)?", line, re.I):
            section = "ing"
            continue
        if re.match(r"(\*\*)?(steps|directions):(\*\*)?", line, re.I):
            section = "step"
            continue

        # Collect bullet or numbered lines
        if section == "ing":
            # either "- item" or plain "1 can item"
            if line.startswith("- "):
                ing.append(line[2:].strip())
            else:
                ing.append(line)
        elif section == "step":
            # either "1. Do this" or plain sentences
            m = re.match(r"^\d+\.\s+(.*)", line)
            if m:
                steps.append(m.group(1).strip())
            else:
                steps.append(line)

    # Remove any empty entries
    ing = [i for i in ing if i]
    steps = [s for s in steps if s]
    if not ing or not steps:
        return None

    # Normalize ingredient units if desired
    ing = [normalize_ingredient(i) for i in ing]

    return {
        "title":       title,
        "ingredients": ing,
        "steps":       steps
    }

def extract_recipes(txt_path):
    raw = normalize(txt_path.read_text(encoding="utf-8", errors="ignore"))
    lines = raw.splitlines()
    recipes, buf = [], []
    current_title = None

    for line in lines:
        if is_recipe_title(line):
            # flush previous
            if current_title:
                parsed = parse_sections(current_title, buf)
                if parsed:
                    recipes.append(parsed)
            current_title, buf = line.strip(), []
        elif current_title:
            buf.append(line)

    # flush last one
    if current_title:
        parsed = parse_sections(current_title, buf)
        if parsed:
            recipes.append(parsed)

    return recipes

def normalize_ingredient(ing: str) -> str:
    """Standardize units and fractions in a single ingredient line."""
    # Expand common unit shorthands
    unit_map = {
        r"\bc\.?\b": "cup",
        r"\bT\.?\b": "tbsp",
        r"\bt\.?\b": "tsp",
        # add more as needed
    }
    for pat, rep in unit_map.items():
        ing = re.sub(pat, rep, ing, flags=re.I)
    # Normalize fractions
    ing = ing.replace("½", "1/2").replace("¼", "1/4")
    return ing

def main():
    count = 0
    with OUT_PATH.open("w", encoding="utf-8") as fout:
        for txt_path in RAW_DIR.glob("*.txt"):
            raw = normalize(txt_path.read_text(encoding="utf-8", errors="ignore"))
            # split into title+buf (you already have extract_recipes)
            recipes = extract_recipes(txt_path)
            for rec in recipes:
                # rec is {"title": ..., "ingredients": [...], "steps": [...]}
                # Build a single text field with markers:
                text = "<|startofrecipe|>\n"
                text += f"TITLE: {rec['title']}\n"
                text += "<|ingredients|>\n"
                for i in rec["ingredients"]:
                    text += f"- {i}\n"
                text += "<|steps|>\n"
                for s in rec["steps"]:
                    text += f"{s}\n"
                text += "<|endofrecipe|>\n"
                fout.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
                count += 1
    print(f"✓ Wrote {count} recipes with markers to {OUT_PATH}")


if __name__ == "__main__":
    main()