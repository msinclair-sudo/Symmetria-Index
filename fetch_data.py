import json
import requests
import time
import argparse
import sys

"""
USDA FoodData Central → ingredient nutrient harvester (v2)
---------------------------------------------------------
• Captures **serving_size** as  {"value": float, "unit": "g"}  (whatever unit USDA gives).
• For every nutrient we track, stores **both** the numeric value and its unit:
      "protein": {"value": 0.26, "unit": "G"}
  Units map 1‑to‑1 with USDA `unitName`. No unit math here—the metadata
  file (maintained separately) will describe each unit and its base‑gram
  conversion factor.
• Keys remain unit‑less (e.g. `protein`, `calcium`).
• Two modes:
      default → fills ALL ingredients   → writes `ingredients_filled.json`
      --test Apple → fills Apple only  → writes `test_Apple_raw.json`, `test_Apple_parsed.json`

"""

# ---------------------- CLI -------------------------------------------------
parser = argparse.ArgumentParser(description="Populate ingredient nutrient data from USDA FoodData Central (FDC)")
parser.add_argument('--test', metavar='INGREDIENT', help='Name of a single ingredient to test and save raw/parsed output')
args = parser.parse_args()
TEST_ING = args.test.lower() if args.test else None

# ---------------------- load mappings from JSON -----------------------------
try:
   with open('nutrient_ID_map.json', 'r', encoding='utf-8') as nf:
       raw_map = json.load(nf)
       NUTRIENT_ID_MAP = {}
       for k, entry in raw_map.items():
           try:
               path = entry['path']        # your new format: a list of keys
           except (TypeError, KeyError):
               # (optional) warn or skip entries without a "path"
               continue
           NUTRIENT_ID_MAP[int(k)] = path
except FileNotFoundError:
    sys.exit('ERROR: nutrient_ID_map.json not found')

try:
    with open('units_meta.json', 'r', encoding='utf-8') as uf:
        UNITS_META = json.load(uf)
except FileNotFoundError:
    sys.exit('ERROR: units_meta.json not found')

# ---------------------- API key --------------------------------------------
try:
    with open('key.txt', 'r', encoding='utf-8') as fh:
        API_KEY = fh.read().strip()
except FileNotFoundError:
    sys.exit('ERROR: key.txt not found — put your USDA API key in that file')
if not API_KEY:
    sys.exit('ERROR: key.txt is empty — paste your USDA API key on line 1')

SEARCH_URL = 'https://api.nal.usda.gov/fdc/v1/foods/search'

# ---------------------- helper ---------------------------------------------
def ensure_dict_path(d: dict, *keys):
    """Drill into nested dicts, creating as needed, and return leaf dict."""
    for k in keys:
        d = d.setdefault(k, {})
    return d

# ---------------------- load ingredient skeleton ---------------------------
with open('ingredients.json', 'r', encoding='utf-8') as fh:
    ingredients = json.load(fh)

name_to_entry = {ing['name'].lower(): ing for ing in ingredients}

# ---------------------- main loop ------------------------------------------
total = 1 if TEST_ING else len(ingredients)
for idx, (name_lc, ing) in enumerate(name_to_entry.items(), start=1):
    if TEST_ING and name_lc != TEST_ING:
        continue

    print(f"[{idx}/{total}] {ing['name']} …", end='')
    params = {'api_key': API_KEY, 'query': ing['name'], 'pageSize': 1}

    try:
        resp = requests.get(SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        food = resp.json()['foods'][0]
    except Exception as exc:
        print(f" ERROR ({exc})")
        continue

    # serving size
    size_val = food.get('servingSize')
    size_unit = food.get('servingSizeUnit') or 'g'
    if size_val is not None:
        ing['serving_size'] = {'value': float(size_val), 'unit': size_unit}

    # nutrients
    for fn in food.get('foodNutrients', []):
        nid = fn['nutrientId']
        path = NUTRIENT_ID_MAP.get(nid)
        if not path:
            continue
        val = fn.get('value')
        unit = fn.get('unitName', '').upper()
        if val is None:
            continue
        leaf_parent = ensure_dict_path(ing, *path[:-1])
        leaf_parent[path[-1]] = {'value': float(val), 'unit': unit}

    if TEST_ING:
        with open(f'test_{ing["name"]}_raw.json', 'w', encoding='utf-8') as rh:
            json.dump(food, rh, indent=2)
        with open(f'test_{ing["name"]}_parsed.json', 'w', encoding='utf-8') as ph:
            json.dump(ing, ph, indent=2)
        print(" saved test files and exiting test mode.")
        break

    print(" done.")
    time.sleep(0.5)

# save all
if not TEST_ING:
    with open('ingredients_filled.json', 'w', encoding='utf-8') as out:
        json.dump(ingredients, out, indent=2)
    print(f"Saved nutrient data for {len(ingredients)} ingredients → ingredients_filled.json")
