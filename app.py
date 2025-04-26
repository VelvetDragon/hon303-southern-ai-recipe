# app.py

import os
import json
import re
import time
import requests
from requests.exceptions import HTTPError
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from src.search import search_local

# 1. Load environment variables from .env
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv("HF_MODEL")

# 2. Use the text2text-generation pipeline endpoint with wait_for_model
HF_API = f"https://api-inference.huggingface.co/pipeline/text2text-generation/{HF_MODEL}"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# 3. Generation parameters for the T5 recipe model
GEN_KWARGS = {
    "max_length": 512,
    "min_length": 64,
    "no_repeat_ngram_size": 3,
    "do_sample": True,
    "top_k": 60,
    "top_p": 0.95
}

def parse_plain_recipe(raw: str) -> dict:
    """
    Parse free text of the form:
      "title: X ingredients: A, B directions: Step1. Step2."
    into a dict with keys title, ingredients (list), steps (list).
    """
    txt = " " + raw.replace("\n", " ").strip() + " "
    # Extract title
    m1 = re.search(r"\stitle:\s*(.*?)\s+ingredients:", txt, re.I|re.S)
    title = m1.group(1).strip() if m1 else ""
    # Extract ingredients
    m2 = re.search(r"\singredients:\s*(.*?)\s+directions:", txt, re.I|re.S)
    ingr_text = m2.group(1).strip() if m2 else ""
    # Extract directions
    m3 = re.search(r"\sdirections:\s*(.*)", txt, re.I|re.S)
    dirs_text = m3.group(1).strip() if m3 else ""

    # Split ingredients on commas or semicolons
    ingredients = [i.strip() for i in re.split(r"[;,]", ingr_text) if i.strip()]
    # Split steps on periods
    steps = []
    for s in dirs_text.split("."):
        s = s.strip()
        if s:
            steps.append(s + ".")
    return {"title": title, "ingredients": ingredients, "steps": steps}

def call_hf_model(query: str) -> dict:
    """
    Calls the HF text2text-generation pipeline for recipes.
    Always returns a dict containing 'source' and either 'recipe' (dict) or 'message'.
    """
    payload = {
        "inputs": "items: " + query.strip(),
        "options": {"wait_for_model": True},
        "parameters": GEN_KWARGS
    }

    for attempt in range(3):
        try:
            resp = requests.post(HF_API, headers=HF_HEADERS, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            text = (
                data[0].get("generated_text", "")
                if isinstance(data, list)
                else data.get("generated_text", "")
            )

            # 1) Try JSON parse if model returned JSON
            start = text.find("{")
            end   = text.rfind("}")
            if start != -1 and end != -1:
                snippet = text[start:end+1]
                try:
                    j = json.loads(snippet)
                    return {
                        "source": "ai",
                        "recipe": {
                            "title": j.get("title", "").strip(),
                            "ingredients": j.get("ingredients", []),
                            "steps": j.get("directions", j.get("steps", []))
                        }
                    }
                except (ValueError, json.JSONDecodeError):
                    pass  # fall through to plain-text parsing

            # 2) Fallback: parse the plain-text format
            parsed = parse_plain_recipe(text)
            return {"source": "ai", "recipe": parsed}

        except HTTPError as e:
            status = e.response.status_code if e.response else None
            # Retry on server errors
            if status and 500 <= status < 600:
                time.sleep(2 ** attempt)
                continue
            return {"source": "error", "message": f"HF Error {status}: {e}"}
        except Exception as e:
            return {"source": "error", "message": f"Unexpected error: {e}"}

    return {"source": "error", "message": "HF unavailable after retries."}

# --- Flask application ---

app = Flask(__name__)

@app.route("/api/recipe")
def get_recipe():
    """
    GET /api/recipe?q=<query>
    1) First attempts a local fuzzy search.
    2) If no local matches, falls back to the AI model.
    Always returns JSON with a 'source' key.
    """
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Please provide ?q=<dish or ingredient list>"}), 400

    # Local search
    local = search_local(q)
    if local:
        results = [
            {
                "title": r["title"],
                "ingredients": r["ingredients"],
                "steps": r["steps"],
                "score": score
            }
            for r, score in local
        ]
        return jsonify({"source": "local", "recipes": results})

    # AI fallback
    ai_res = call_hf_model(q)
    status = 200 if ai_res.get("source") == "ai" else 502
    return jsonify(ai_res), status

if __name__ == "__main__":
    app.run(debug=True, port=5000)
