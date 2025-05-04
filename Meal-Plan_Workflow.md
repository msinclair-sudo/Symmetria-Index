## Meal‑Plan Workflow Blueprint — **Interactive, Token‑Aware & Strict**

This blueprint *supersedes* the previous single‑dump version.  
It **retains every MUST / MUST NOT guard‑rail** while introducing an interactive, low‑token conversation flow and a two‑step final export.

---

### 0. Phase Map & Conversation Flow

| Phase | Assistant **MUST** output | User **MUST** reply | Max payload |
|-------|---------------------------|---------------------|-------------|
| **A** Validate data | JSON `{phase:"A",status:"ok"\|"error",failed_checks:[…]}` | `continue` **OR** corrections | ≤ 1 k |
| **B** Pick goal | Goal list → user chooses | chosen goal key | ≤ 0.5 k |
| **C** Score recipes (light) | Top‑N table (ID, score, cost) | `continue` / pin / swap | ≤ 2 k |
| **D** Draft menu skeleton | `cooking_sessions`, `daily_meals` **IDs only**, `nutrition_snapshot` | `continue` / tweak | ≤ 3 k |
| **E** Nutrition evaluation | pass/fail + warnings table | `continue` / adjust | ≤ 2 k |
| **F1** **Plan dump #1 (MANDATORY)** | Full plan **minus** `recipes_full` **PLUS** `shopping_list` | `continue` | ≤ 6 k |
| **F2** **Plan dump #2 (MANDATORY)** | Stand‑alone JSON `{ "recipes_full": { … } }` | — | up to limit |
| **G** Optional extras | micronutrient grid, cost charts, PDF … | — | varied |

> **Protocol MUST**: Every phase ends with the prompt  
> *“Type `continue` to proceed or suggest changes.”*

---

### 1. Phase A — Load & Validate the Data  **(MUST pass before planning)**

| File | Purpose | Mandatory checks (error → abort) |
|------|---------|----------------------------------|
| **ingredients.json** | Master nutrition & price table | • Every ingredient referenced by any recipe **MUST** exist here.<br>• All macro/micro values **MUST** keep their unit strings (e.g. `"21g"`) **in the file** but **MUST** parse to pure numbers for calculations.<br>• All numeric values written back to any JSON file **MUST** be enclosed in quotes. |
| **recipes.json** | Menu catalogue | • Ingredient names **MUST** match `ingredients.json` exactly (case‑sensitive).<br>• `nutrition_summary` **MUST** be complete; if missing, assistant recalculates and injects it.<br>• `cost_per_serving` **MUST** be computed (Σ ingredient‑cost ÷ servings). |
| **goals.json** | Optimisation weight vectors | • At least four goals **MUST** be present.<br>• All weights **MUST** be numeric strings between –1 and +1. |
| **profile.json** | Personal targets & constraints | • Keys `DailyNutritionalNeeds`, `WeeklyNutritionalNeeds`, `cook_sessions_per_week` **MUST** exist.<br>• `cook_sessions_per_week` **MUST** equal `"3"`. |

*If **any** check fails, the assistant **MUST** reply:*

```json
{ "error": "load-validation-failed", "details": "<short description>" }
```

After a successful validation the assistant **MUST** emit the Phase‑A envelope and prompt the user.

---

### 2. Phase B — Select the Weekly Goal

1. The assistant **MUST** list all goal keys plus their description.  
2. The user **MUST** explicitly choose one (blending not allowed).  
3. The choice is echoed as `"goal_used"`; weights copied to `"goal_weights"`.  
4. If the user requests an unknown goal the assistant **MUST** reply:

```json
{ "error": "unknown-goal", "details": "Requested goal not found in goals.json" }
```

---

### 3. Phase C — Recipe Scoring

**Formula (MUST use):**

```
score =
    Σ_i [(recipe_nutrient_i / daily_target_i) × goal_weight_i]
  + 0.5 × (#matching_tags) − 0.5 × (#conflicting_tags)
  − 1   if cost_per_serving > $5 AUD
```

The assistant **MUST** calculate scores for every recipe **once** and return only the **top 15** lines during Phase C.  
The full `scoring_log` **MUST** be kept for the final dumps.

---

### 4. Phase D — Draft Menu Skeleton

#### 4.1 Cooking‑Session Rules — **MUST NOT be broken**

| Rule | Description |
|------|-------------|
| **C1** | Exactly **3** cooking sessions on user‑friendly days (default Sun/Tue/Thu). |
| **C2** | Each session cooks 2–3 recipes; leftovers **MUST** populate subsequent days. |
| **C3** | A meal **MUST NOT** be scheduled > 2 days after its cooking session. |
| **C4** | Weekday breakfasts **MUST** satisfy at least one: `cook_time = "0"` **OR** `prep_time ≤ "15"` **OR** `"overnight"` tag. |
| **C5** | `cost_per_serving` for every meal **MUST** be ≤ **$5 AUD**. |
| **C6** | If a recipe has `"max_leftover_days"`, leftovers **MUST NOT** exceed that value (smaller of 2 days or recipe‑specific limit). |

During Phase D the assistant **MUST** output **real numbers, no placeholders**:

```jsonc
{
  "phase": "D",
  "cooking_sessions": [
    { "id": "CS1", "day": "Sunday",   "recipes": ["Chickpea Curry","Oat Pancakes"] },
    { "id": "CS2", "day": "Tuesday",  "recipes": ["Lentil Soup","Southwest Tofu Scramble"] },
    { "id": "CS3", "day": "Thursday", "recipes": ["Sweet Potato Chili","Banana Oat Smoothie"] }
  ],
  "daily_meals": {
    "Monday":    ["Chickpea Curry","Oat Pancakes","Chickpea Curry"],
    "Tuesday":   ["Sweet Potato Chili","Southwest Tofu Scramble","Sweet Potato Chili"],
    "Wednesday": ["Lentil Soup","Oat Pancakes","Lentil Soup"],
    "Thursday":  ["Sweet Potato Chili","Southwest Tofu Scramble","Sweet Potato Chili"],
    "Friday":    ["Lentil Soup","Oat Pancakes","Lentil Soup"],
    "Saturday":  ["Chickpea Curry","Banana Oat Smoothie","Chickpea Curry"],
    "Sunday":    ["Sweet Potato Chili","Southwest Tofu Scramble","Sweet Potato Chili"]
  },
  "nutrition_snapshot": {
    "Calories":             "2095",
    "Protein":              "82",
    "Carbohydrates":        "286",
    "Fat":                  "63",
    "Fiber":                "34",
    "EstimatedCostPerDay":  "$4.72"
  }
}
```

nutrition_snapshot **MUST** contain at least Calories, Protein, Carbohydrates, Fat, Fiber and EstimatedCostPerDay — all as strings with units stripped (except the cost).
Zero { … } placeholders are allowed in Phase D.

---

### 5. Phase E — Evaluate Menus vs Profile

The assistant **MUST** enforce all original hard limits:

* Daily `"Calories"` outside ±10 % → **fail**  
* Daily `"Fiber"` < target → **fail**  
* Any of the following key micronutrients—`VitaminC`, `Iron`, `Calcium`, `Magnesium`, `Zinc`—below 90 % of target → **fail**  
* `weekly.Calories` outside ±5 % → **fail**  
* Any breakfast violates Rule C4 → **fail**  
* Any meal scheduled before its cook date or > 2 days after → **fail**  
* Any `cost_per_serving` > $5 AUD → **fail**

Phase E output **MUST** be:

```jsonc
{ "phase":"E", "status":"pass"|"fail", "warnings":[ … ] }
```

---

### 6. Phase F — **Two‑Step Final Export (STRICT)**

#### 6.1 Dump #1 (Phase F1) — **MUST** include shopping_list, **MUST NOT** include recipes_full
*(See JSON skeleton earlier.)*

#### 6.2 Dump #2 (Phase F2)”** and insert the bullet **immediately after** the opening description (before the code fence).

*Every value under `recipes_full` **MUST** be a verbatim recipe object that contains at minimum the keys  
`"Category"`, `"Cuisine"`, `"Servings"`, `"Ingredients"`, `"Instructions"` and `"NutritionSummary"`.  
Using the literal `{ … }` placeholder is **forbidden**.*

Before sending Phase F2, the assistant **MUST** scan each recipe object. If any object is missing one of the required fields the assistant MUST abort with

*If either dump is invalid the assistant **MUST** reply:*

```json
{ "error": "export-validation-failed", "details": "<reason>" }
```

---

### 7. Phase G — Optional Post‑Export Services

After Phase F2 the assistant **MAY** offer extras (micronutrient grid, cost charts, PDF) but **MUST NOT** modify any previously emitted JSON artefact.

---

### 8. Validation Gates (MUST run)

* **Phase A** → Section 1 checks  
* **Phase E** → Section 5 limits  
* **Phase F2** → Original §8 **plus**: ensure `shopping_list` present in F1 and `recipes_full` present in F2
  * `recipes_full` **MUST NOT** contain placeholder objects. If any recipe object lacks required keys the assistant **MUST** abort with
    ```json
    { "error": "export-validation-failed", "details": "recipes_full contains placeholders" }
    ```

---

### 9. Developer Notes (Non‑normative)

* `shopping_list` merges like ingredients; units stay strings.  
* If `recipes_full` approaches model token limit in F2, split over consecutive messages.

---

*End of Interactive, Multi‑Dump Blueprint*    