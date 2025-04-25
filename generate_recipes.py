#!/usr/bin/env python
# generate_recipes.py


import argparse
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import PeftModel

def load_model(adapter_dir: str, base_model: str = "EleutherAI/gpt-neo-125M"):
    # 1) 8-bit quant config (if you have CUDA)
    bnb_config = BitsAndBytesConfig(load_in_8bit=True, llm_int8_threshold=6.0) \
        if torch.cuda.is_available() else None

    # 2) Load base
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto" if torch.cuda.is_available() else None,
        low_cpu_mem_usage=True,
    )

    # 3) Tokenizer
    tok = AutoTokenizer.from_pretrained(base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
        base.config.pad_token_id = tok.eos_token_id

    # 4) Attach your LoRA adapter
    model = PeftModel.from_pretrained(base, adapter_dir, torch_dtype=base.dtype)
    model.eval()
    return model, tok

def generate_recipe(title: str,
                    model,
                    tok,
                    max_new_tokens: int,
                    temperature: float,
                    top_p: float):
    # Seed with both markers up front:
    prompt = (
        "<|startofrecipe|>\n"
        f"TITLE: {title}\n"
        "<|ingredients|>\n"
        "<|steps|>\n"
    )
    inputs = tok(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        model.cuda()
        inputs = {k: v.cuda() for k, v in inputs.items()}

    out = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        top_p=top_p,
        eos_token_id=tok.eos_token_id,
        pad_token_id=tok.pad_token_id,
        do_sample=True,
    )
    text = tok.decode(out[0], skip_special_tokens=False)
    return text

def clean(text: str):
    # Keep everything from the start marker through the end marker (if generated)
    if "<|endofrecipe|>" in text:
        text = text.split("<|endofrecipe|>")[0] + "<|endofrecipe|>"
    # Otherwise just strip trailing partial tokens
    return text.strip()

def main():
    p = argparse.ArgumentParser("Generate a Southern recipe")
    p.add_argument("--model_dir", default="southern-recipe-model",
                   help="Folder with adapter_model.safetensors etc.")
    p.add_argument("--prompt",   required=True, help="Recipe title")
    p.add_argument("--max_new_tokens", type=int,   default=200)
    p.add_argument("--temperature",    type=float, default=0.8)
    p.add_argument("--top_p",          type=float, default=0.95)
    args = p.parse_args()

    model, tok = load_model(args.model_dir)
    raw = generate_recipe(
        args.prompt,
        model, tok,
        args.max_new_tokens,
        args.temperature,
        args.top_p,
    )
    print("\n" + clean(raw) + "\n")

if __name__ == "__main__":
    main()
