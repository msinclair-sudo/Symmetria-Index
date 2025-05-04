## Meal‑Plan Workflow Blueprint — Markdown Version

---

### 1. Load & Validate the Data — **MUST pass before planning**

| File | Purpose | Mandatory checks (error → abort) |
|------|---------|----------------------------------|
| **ingredients.json** | Master nutrition & price table | • Every ingredient referenced by any recipe **MUST** exist here.<br>• All macro/micro values **MUST** keep their unit strings (e.g. `"21g"`) **in the file** but **MUST** parse to pure numbers for calculations.<br>• All numeric values written back to any JSON file **MUST** be enclosed in quotes. |
| **recipes.json** | Menu catalogue | • Ingredient names **MUST** match `ingredients.json` exactly (case‑sensitive).<br>• `nutrition_summary` **MUST** be complete; if missing, assistant recalculates and injects it.<br>• `cost_per_serving` **MUST** be computed (Σ ingredient‑cost ÷ servings). |
| **goals.json** | Optimisation weight vectors | • At least four goals **MUST** be present.<br>• All weights **MUST** be numeric strings between –1 and +1. |
| **profile.json** | Personal targets & constraints | • Keys `DailyNutritionalNeeds`, `WeeklyNutritionalNeeds`, `cook_sessions_per_week` **MUST** exist.<br>• `cook_sessions_per_week` **MUST** equal `"3"`. |

**Validation gate**  
If *any* check fails, reply:

```json
{ "error": "load-validation-failed", "details": "<short description>" }
```

---

### 2. Select the Weekly Goal — **make provenance explicit**

1. Choose exactly **one** goal from `goals.json` (blending not allowed).  
2. Record it as `"goal_used"` in the final plan.  
3. Copy the full weight vector into `"goal_weights"` (object) so the user can audit optimisation inputs. `"goal_weights"` is **REQUIRED** in the final JSON.  
4. If the requested focus (e.g. “gut health”) does not match any key, return:

```json
{ "error": "unknown-goal", "details": "Requested goal not found in goals.json" }
```

---

### 3. Recipe Scoring — **deterministic & auditable**

```
score =
  Σ_i [(recipe_nutrient_i / daily_target_i) × goal_weight_i]   // nutrition term
+ (tag_bonus_sum)                                             // +0.5 per *matching*, −0.5 per *conflicting*
− (cost_penalty)                                              // +1 penalty if cost_per_serving > $5 AUD
```

**Tag bonus logic**  

*Define once:*  

* `matching_tags` = `goal.tags` ∪ `profile.preferred_tags`  
* `conflicting_tags` = `profile.avoid_tags`  

Add **+0.5** for every tag present in `matching_tags`; subtract **0.5** for each in `conflicting_tags`.

**Recording**  
Store each recipe’s `score` and `cost_per_serving` in a `scoring_log` object embedded under `"debug" → "scoring_log"` in the final JSON.

---

### 4. Generate Candidate Weekly Menus

#### 4.1 Cooking‑Session Rules — **MUST NOT be broken**

| Rule | Description |
|------|-------------|
| C1 | Exactly **3** cooking sessions on user‑friendly days (default Sun/Tue/Thu). |
| C2 | Each session cooks 2–3 recipes; leftovers **MUST** populate subsequent days. |
| C3 | A meal **MUST NOT** be scheduled > 2 days after its cooking session. |
| C4 | Weekday breakfasts **MUST** satisfy at least one: `cook_time = "0"` **OR** `prep_time ≤ "15"` **OR** `"overnight"` tag. |
| C5 | `cost_per_serving` for every meal **MUST** be ≤ **$5 AUD**. |
| C6 | If a recipe has `"max_leftover_days"`, leftovers **MUST NOT** exceed that value (smaller of 2 days or recipe‑specific limit). |

If a new recipe is introduced, include its full JSON in a `"new_recipes"` array inside the final plan.

#### 4.2 Fill 21 meal slots

*Follow the anchor‑recipe heuristic.* Each leftover meal entry **MUST** include `"source_cook_session_id"` and `"servings"` so provenance is auditable. Abort a candidate menu immediately if any rule C1–C6 is violated and continue searching.

---

### 5. Evaluate Menus vs Profile — **hard thresholds**

Reject a candidate menu if **any** of the following is true:

* Daily `"Calories"` outside ±10 % of target (compare numeric values after stripping `"kcal"`).  
* Daily `"Fiber"` < target.  
* Any **key micronutrient** (Vitamin C, Iron, Calcium, Magnesium, Zinc) < 90 % of target (compare numeric values, ignore unit strings).  
* `weekly.Calories` outside ±5 % of weekly target.  
* `cooking_sessions.length` ≠ `"3"`.  
* Any breakfast violates Rule C4.  
* Any meal placed before its cook date (Rule C3).  
* Any meal `cost_per_serving` > `"$5"`.

If no candidate passes, reply:

```json
{ "error": "no-valid-menu", "details": "Failed evaluation step" }
```

---

### 6. Output Contract — **must be obeyed**

1. **Reply format**  
   * The assistant’s **entire** reply **MUST** be one fenced JSON block  
     ```json
     { … }
     ```
   * There is **no prose**, headings, or Markdown outside the fence.

2. **File‑name rule**  
   * The first key in the JSON **MUST** be  
     ```json
     "file_name": "meal_plan_<week_start>.json"
     ```
   * Replace `<week_start>` with the Monday start date (ISO yyyy‑mm‑dd).

3. **Required top‑level keys** (order irrelevant)  

```
file_name            (string)
week_start           (string, ISO date)
goal_used            (string, in goals.json)
goal_weights         (object)
diet_profile_digest  (object)   ← proof profile was read
cooking_sessions     (array, length = 3)
daily_meals          (object, 7 keys Monday → Sunday)
nutrition_summary    (object with daily & weekly)
recipes_full         (object)   ← **NEW: full recipe blocks**
debug                (object)   ← at minimum scoring_log

```

4. **Optional keys**  

* `new_recipes` — required only if new recipes were introduced.

#### recipes_full schema  — **embed full recipe objects**
```json
"recipes_full": {
  "<recipe_id>": {
    // entire recipe copied verbatim from recipes.json
  },
  "<another_recipe_id>": { … }
}
```
* Every recipe appearing in `daily_meals` **MUST** be present here verbatim.  
* If `new_recipes` exists, copy those objects into `recipes_full` too.  
* Do **not** remove or rename any recipe fields.


5. **diet_profile_digest**  
   Put exact numeric targets pulled from **profile.json**, e.g.

```json
"diet_profile_digest": {
  "Calories_target": "2100",
  "Fiber_target": "30",
  "Cook_sessions_per_week": "3"
}
```

6. **Schema snippets**  

```json
"daily_meals": {
  "Monday": {
    "breakfast": { "recipe_id": "BircherMuesli", "servings": "1" },
    "lunch":     { "recipe_id": "LentilSoup",    "servings": "1" },
    "dinner":    { "recipe_id": "Chili",         "servings": "1", "source_cook_session_id": "2" }
  }
  …
}
```

7. **Numbers as strings**  
   *All* numeric literals written to the plan **MUST** be strings (e.g. `"450"` not `450`).

8. **Validation gate (final)**  
   Before emitting, run all rules in §1, §4, and §5; if any fail, respond:

```json
{ "error": "export-validation-failed", "details": "<reason>" }
```

---

*End of Blueprint*
