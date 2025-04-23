# src/model_training/prepare_data.py
import json, random, pathlib

INPUT     = pathlib.Path("data/processed/recipes_clean.jsonl")
TRAIN_OUT = pathlib.Path("data/processed/finetune/train.jsonl")
VAL_OUT   = pathlib.Path("data/processed/finetune/val.jsonl")
VAL_FRAC  = 0.1  # 10% for validation

# Load and shuffle
records = [json.loads(line) for line in INPUT.open(encoding="utf-8")]
random.shuffle(records)

# Split
n_val       = int(len(records) * VAL_FRAC)
val_records = records[:n_val]
train_records = records[n_val:]

def format_text(r: dict) -> str:
    parts = []
    parts.append(f"### {r['title']}")
    parts.append("Ingredients:")
    parts += r.get("ingredients", []) if "ingredients" in r else []
    parts.append("Steps:")
    parts += r.get("steps", []) if "steps" in r else r["body"].splitlines()
    return "\n".join(parts)

# Ensure output dir exists
TRAIN_OUT.parent.mkdir(parents=True, exist_ok=True)

# Write JSONL with a single “text” field
for path, subset in [(TRAIN_OUT, train_records), (VAL_OUT, val_records)]:
    with path.open("w", encoding="utf-8") as fout:
        for rec in subset:
            text = format_text(rec)
            fout.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")

print(f"Saved {len(train_records)} training and {len(val_records)} validation examples")
