# Re-use your test script but with "biscuits" instead
# Create test_search_biscuits.py alongside test_search.py:

# test_search_biscuits.py
from src.search import search_local

if __name__ == "__main__":
    matches = search_local("biscuits")
    if not matches:
        print("No biscuit matches found.")
    else:
        for rec, score in matches:
            print(f"{score:.1f} — {rec['title']}")
