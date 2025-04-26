# generate_recipes.py
import argparse, json, pathlib, torch
from rapidfuzz import process
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel

# 1) Load your cleaned recipes as ground truth
RECIPES_FILE = pathlib.Path("data/processed/recipes_clean.jsonl")
title_map = {}
for line in RECIPES_FILE.read_text(encoding="utf-8").splitlines():
    r = json.loads(line)
    key = r["title"].strip().lower()
    title_map[key] = {"title": r["title"], "ingredients": r["ingredients"], "steps": r["steps"]}

def find_best_title(q):
    match, score = process.extractOne(q, list(title_map.keys()))
    return match if score >= 80 else None

# 2) Model loader (lazy)
_model, _tok = None, None
def load_model(model_dir):
    global _model, _tok
    if _model is None:
        bnb = BitsAndBytesConfig(load_in_8bit=True) if torch.cuda.is_available() else None
        _tok = AutoTokenizer.from_pretrained(model_dir)
        _model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            quantization_config=bnb,
            device_map="auto" if bnb else None,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True,
        )
        # if LoRA
        if isinstance(_model, PeftModel):
            _model = _model.merge_and_unload()
    return _model, _tok

# 3) Generate via LLM
def model_generate(model_dir, prompt, max_new_tokens, temp, top_p):
    model, tok = load_model(model_dir)
    inp = prompt.rstrip() + "\n<|ingredients|>\n"
    ids = tok(inp, return_tensors="pt").input_ids.to(model.device)
    out = model.generate(
        ids,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=temp,
        top_p=top_p,
        eos_token_id=tok.eos_token_id,
        pad_token_id=tok.eos_token_id,
    )
    text = tok.decode(out[0], skip_special_tokens=False)
    return text

# 4) Parse the “marker” format back into JSON
def parse_generated(text):
    # Expect: <|startofrecipe|>TITLE: X\n<|ingredients|>\n- ..\n<|steps|>\n1. ..\n<|endofrecipe|>
    parts = {}
    # strip header
    if "<|startofrecipe|>" in text:
        text = text.split("<|startofrecipe|>",1)[1]
    # title
    if "TITLE:" in text:
        title = text.split("TITLE:",1)[1].splitlines()[0].strip()
        parts["title"] = title
    # ingredients
    if "<|ingredients|>" in text and "<|steps|>" in text:
        ing_block = text.split("<|ingredients|>",1)[1].split("<|steps|>",1)[0]
        parts["ingredients"] = [l.strip()[2:].strip() for l in ing_block.splitlines() if l.strip().startswith("- ")]
    # steps
    if "<|steps|>" in text:
        steps_block = text.split("<|steps|>",1)[1]
        # up to end marker
        if "<|endofrecipe|>" in steps_block:
            steps_block = steps_block.split("<|endofrecipe|>",1)[0]
        parts["steps"] = [l.strip().lstrip("0123456789. ").strip() 
                          for l in steps_block.splitlines() 
                          if l.strip()]
    return parts

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model_dir", default="southern-recipe-model")
    p.add_argument("--prompt", required=True)
    p.add_argument("--max_new_tokens", type=int, default=200)
    p.add_argument("--temperature", type=float, default=0.8)
    p.add_argument("--top_p", type=float, default=0.95)
    p.add_argument("--json", action="store_true",
                   help="emit a JSON blob instead of plain text")
    args = p.parse_args()

    q = args.prompt.strip().lower()
    # 1) Exact lookup
    if q in title_map:
        out = title_map[q]
    else:
        # 2) Fuzzy
        best = find_best_title(q)
        if best:
            out = title_map[best]
        else:
            # 3) Generate new
            raw = model_generate(
                args.model_dir, 
                f"<|startofrecipe|>\nTITLE: {args.prompt}\n<|ingredients|>",
                args.max_new_tokens,
                args.temperature,
                args.top_p
            )
            out = parse_generated(raw)

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        # human‐friendly
        print(f"{out['title']}\n\nIngredients:")
        for i in out["ingredients"]:
            print(f"- {i}")
        print("\nSteps:")
        for idx, s in enumerate(out["steps"],1):
            print(f"{idx}. {s}")

if __name__=="__main__":
    main()
