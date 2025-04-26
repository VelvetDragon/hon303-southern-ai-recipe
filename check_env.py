# check_env.py
import os
from dotenv import load_dotenv

print("Before load:", os.getenv("HF_TOKEN"), os.getenv("HF_MODEL"))
load_dotenv()   # explicitly load .env
print(" After load:", os.getenv("HF_TOKEN"), os.getenv("HF_MODEL"))

