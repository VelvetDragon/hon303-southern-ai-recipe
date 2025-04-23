# src/model_training/prepare_data.py

import json, random, pathlib

# 1) Paths
INPUT      = pathlib.Path("data/processed/recipes_clean.jsonl")
TRAIN_OUT  = pathlib.Path("data/processed/finetune/train.jsonl")
VAL_OUT    = pathlib.Path("data/processed/finetune/val.jsonl")
VAL_FRAC   = 0.1  # 10% for validation

# 2) Load & shuffle
records = [
    json.loads(line)
    for line in INPUT.open(encoding="utf-8")
    if line.strip()
]
random.seed(42)
random.shuffle(records)

# 3) Split
n_val        = int(len(records) * VAL_FRAC)
val_records  = records[:n_val]
train_records = records[n_val:]

# 4) Ensure output dir exists
TRAIN_OUT.parent.mkdir(parents=True, exist_ok=True)

# 5) Write out the JSONL splits (each rec already has only a "text" key)
for path, subset in [(TRAIN_OUT, train_records), (VAL_OUT, val_records)]:
    with path.open("w", encoding="utf-8") as fout:
        for rec in subset:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

# 6) Summary
print(f"Loaded     {len(records)} recipes")
print(f"Training   {len(train_records)} → {TRAIN_OUT}")
print(f"Validation {len(val_records)} → {VAL_OUT}")
