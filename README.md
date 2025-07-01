# Symmetria Index - under construction 

Symmetria Index is a structured framework for generating **personalised, nutrient-balanced 7-day meal plans** 

It ships with carefully curated JSON datasets (ingredients, recipes, goals, profile) **and** an interactive, phase-based blueprint that forces the model to ask clarifying questions, validate data, and emit results in small, audit-friendly chunks.

---

## ⚙️ Repository Contents

| File | Purpose |
|------|---------|
| **ingredients.json** | Ingredient-level nutrition & bioactives |
| **recipes.json** | Recipes, tags, nutrition summaries, costs |
| **goals.json** | High-level dietary optimisation vectors |
| **profile.json** | Personal targets & lifestyle constraints |
| **Meal-Plan Workflow Blueprint_Interactive_Strict_v2.md** | **Step-wise LLM playbook** (Phases A → G) |
| **README.md** | You are here |

---

## 🌟 Key Features

* **Metabolic balance** – weights calories, macros & micronutrients  
* **Gut & immune support** – polyphenols, fibre, probiotic tags  
* **Budget guard-rails** – ≤ $5 AUD per serving & cost penalties in scoring  
* **Three cooking sessions / week** – leftovers auto-propagate  
* **Token-efficient interaction** – model must dump data in phases, never in one monolithic blob

---

## 🚀 Quick-start (ChatGPT or other LLM front-end)

1. **Upload** the five JSON files **and** the blueprint markdown into the same chat.  
2. **Prompt once**:  
Follow the instructions in “Meal-Plan_Workflow.md”.


## 3. **Phase A** – The model echoes a validation payload.  
*If any `"failed_checks"` appear, fix your source files and start over.*
4. **Phase B** – The model lists available goals → **you reply with exactly one goal key** (e.g. `GutHealth`).  
5. **Phase C** – Scoring log delivered (silent step, no action).  
6. **Phase D** – Draft meals + `nutrition_snapshot` arrive. Inspect; optionally ask the model to “re-roll Phase D” if you dislike the skeleton.  
7. **Phase E** – Pass/fail evaluation.  
8. **Phase F1** – Final plan **+ shopping list** only.  
**Important:** *type `continue`* to request Phase F2.  
9. **Phase F2** – The assistant streams `recipes_full` in slices until you see  

## 🛠 Troubleshooting
Symptom	Likely cause	Fix
Placeholders { … } in recipes_full	You skipped continue / Phase F2 or blueprint not updated	Type continue or ensure v2 blueprint is loaded
export-validation-failed	A Phase F gate tripped (e.g. placeholder, budget breach)	Read details, revise profile or recipes, restart
Token overflow / assistant stops mid-dump	>40 k-token recipe set	Type continue again; the model must resume next slice

