## Meal-Plan Workflow Blueprint — Markdown Version

---

### 1. Load & Validate the Data

| File                 | Purpose at this stage                         | Key checks                                                                                                 |
| -------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **ingredients.json** | Master nutrition table                        | • Every ingredient used by a recipe must exist here.<br>• Convert macro values (strings) to numbers.       |
| **recipes.json**     | Menu catalogue with per-serving nutrition     | • Ingredient names match `ingredients.json` exactly.<br>• Nutrition summaries are present or recalculated. |
| **goals.json**       | Weights that steer the optimiser              | • Verify four goals exist.<br>• Positive vs negative weights make sense.                                   |
| **profile.json**     | Personal daily / weekly targets & constraints | • Numeric targets for kcal, macros, fiber, key micros.<br>• Flag for `cook_sessions_per_week = 3`.         |

---

### 2. Select the Weekly Goal

Pick one goal from `goals.json` (e.g. **GutHealth** or **HighEnergy**) to drive recipe scoring.  
You can blend goals by combining their weight vectors.

---

### 3. Recipe Scoring Function

normalised_nutrient = recipe_nutrient / daily_target
score = Σ(normalised_nutrient_i × weight_i) + Σ(tag_present? × tag_weight)


---

### 4. Generate Candidate Weekly Menus

#### 4.1 cooking Session Guidelines.

* Choose 3 cooking days
* Cook 2–3 recipes each session (leftovers feed other days).
* Breakfast recipes assigned from Monday to Friday must require minimal effort: they must either 
    1. be no-cook or ready-to-eat
    2. be prepared in under 15 minutes
    3. allow for overnight preparation
* Recipes with "cook_time": "0" are treated as no-cook and can be placed on any day or meal without requiring a prior cooking session
* A meal can not be more than 2 days after it's cooking session. 

#### 4.2 Fill 21 meal slots

1. Pick 3 high-scoring **anchor recipes** suitable for meal-prep.
2. Fill other slots with quick/no-cook recipes.
3. Check ingredient shelf-life heuristics.

### 4.3 RULES  

1. Ensure daily kcal ±10% of 2100 and macros in range

2. No meal may be assigned to a day earlier than its scheduled cooking session. Meals prepared during a cooking session can only be assigned to that day or any later day in the weekly plan.

3. When introducing new recipes not already in recipes.json, always output a recipe code JSON block with the full recipe details (category, cuisine, servings, prep time, cook time, ingredients, instructions, nutrition summary, tags) so it can be appended to recipes.json


---

### 5. Evaluate Menus vs. Profile

For each candidate:

1. Compare daily totals to **DailyNutritionalNeeds**.
2. Compare weekly totals to **WeeklyNutritionalNeeds**.
3. Penalise menus that:

   * Exceed kcal >5%
   * Miss fiber or key micros by >10%
   * Require >3 cooking sessions
   * Assign recipes before their cook day
   * Assign weekday breakfasts that fail minimal-effort rule

Select the highest-scoring valid menu.

---

### 6. Export Meal-Plan File

```json
{
  "week_start": "2025-05-05",
  "cooking_sessions": [
    {
      "day": "Sunday",
      "recipes": [
        { "name": "Hearty Lentil Vegetable Soup", "servings": 4 },
        { "name": "Banana Pancakes", "servings": 2 }
      ]
    },
    {
      "day": "Tuesday",
      "recipes": [
        { "name": "Chicken and Veggie Stir-Fry", "servings": 3 },
        { "name": "Sweet Potato Black Bean Chili", "servings": 4 }
      ]
    },
    {
      "day": "Thursday",
      "recipes": [
        { "name": "Chickpea and Spinach Curry", "servings": 4 }
      ]
    }
  ],
  "daily_meals": {
    "Monday": {
      "Breakfast": { "recipe": "Peanut Butter Banana Oatmeal", "servings": 1 },
      "Lunch":     { "recipe": "Hearty Lentil Vegetable Soup", "servings": 1 },
      "Dinner":    { "recipe": "Chicken and Veggie Stir-Fry", "servings": 1 }
    }
    /* ... repeat for other days ... */
  },
  "nutrition_summary": {
    "daily":   { "Calories": 2080, "Protein": 92,  "Carbohydrates": 290, "Fat": 65, "Fiber": 32 },
    "weekly":  { "Calories": 14560, "Protein": 645, "Carbohydrates": 2030, "Fat": 455, "Fiber": 225 }
  }
}
