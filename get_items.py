import json

# load your recipes (assumed to be a dict of recipe‐objects)
with open('recipes.json', encoding='utf-8') as f:
    recipes = json.load(f)

names = {
    ing.get('item', ing.get('name'))
    for recipe in recipes.values()
    for ing in recipe.get('Ingredients', [])    # use .get to avoid KeyError
}

skeleton = [{"name": n} for n in sorted(names, key=str.lower)]

with open('ingredients.json', 'w', encoding='utf-8') as out:
    json.dump(skeleton, out, indent=2, ensure_ascii=False)
