# src/model_training/prepare_data.py

import json, random, pathlib

INPUT     = pathlib.Path("data/processed/recipes_clean.jsonl")
TRAIN_OUT = pathlib.Path("data/processed/finetune/train.jsonl")
VAL_OUT   = pathlib.Path("data/processed/finetune/val.jsonl")
VAL_FRAC  = 0.1  # 10% validation

# Load & shuffle
records = [json.loads(line) for line in INPUT.open(encoding="utf-8")]
random.shuffle(records)

# Split
n_val        = int(len(records) * VAL_FRAC)
val_records  = records[:n_val]
train_records = records[n_val:]

def format_text(r: dict) -> str:
    # We expect each record to already have "text" with our markers.
    return r["text"]

# Ensure output dir exists
TRAIN_OUT.parent.mkdir(parents=True, exist_ok=True)

# Write out
for path, subset in [(TRAIN_OUT, train_records), (VAL_OUT, val_records)]:
    with path.open("w", encoding="utf-8") as fout:
        for rec in subset:
            fout.write(json.dumps({"text": format_text(rec)}, ensure_ascii=False) + "\n")

print(f"Saved {len(train_records)} train + {len(val_records)} val examples")
