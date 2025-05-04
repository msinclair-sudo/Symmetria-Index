##  Symmetria Index
Symmetria Index is a structured framework for generating personalized, nutrient-balanced meal plans using large language models (LLMs) like ChatGPT.

It provides curated datasets of ingredients, recipes, nutrition goals, and individual profiles, enabling AI-driven meal planning that prioritizes metabolic health, satiety, immune support, and affordability.

# Features
 Structured JSON files for:

Ingredients with nutritional profiles
Recipes with serving details and nutrition summaries
Personal nutrition targets and lifestyle constraints
High-level dietary goals with weighted nutrients and tags
 Focus on metabolic balance, gut health, and immune support
 Budget-friendly recipes
 Scientifically plausible nutrient estimates

# Repository Contents
/ingredients.json                 → Ingredient-level nutritional profiles  
/recipes.json                     → Recipe details and nutrition summaries  
/goals.json                       → Dietary goals and weighted nutrients  
/profile.json                     → Personal nutrition targets and constraints  
/Meal-Plan Workflow Blueprint.md  → Guide for generating 7-day meal plans

# How It Works
Configure your profile, or use default.
Provide all files as input to an LLM.
Prompt the LLM: "follow the instruction in the markdown"
The first response should be to provide it with a goal. if it doesn't list the goals, ask what the goals are. 

the LLM will ask questions for your meal plan.
Receive an output file meal_plan_yyyy-MM-dd.json with:
21 meal slots (breakfast, lunch, dinner)

# Cooking sessions
Daily & weekly nutrition summaries

# Example Use Cases
Personalized weekly meal plans
Recipe generation aligned with metabolic goals
Ingredient balancing and shopping list optimization
Dietary analysis and improvement suggestions

License
Creative Commons Legal Code

# Contributing
Contributions are welcome! Please submit pull requests for:
Additional affordable, diverse recipes
New ingredient profiles with full nutritional data
Improvements to workflows or documentation

# Project Maintainers
msinclair-sudo
