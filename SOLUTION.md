# Backend Developer Case Study — Recipe Sharing API


## Part A — Meal Planning
* For all endpoint, authentication is required
* Meal Plan belongs to an user
* A Meal Plan shoukd cover Monday-Sunday
* Each day has multiple slots assigned a recipe

### Model

#### Tables

* meal_plan
    - id (PK)
    - user_id (FK user)
    - name
    - created_at
    - updated_at

* meal_plan_items
    - id (PK)
    - meal_plan_id (FK meal_plan)
    - day_of_week
    - slot 
    - recipe_id (FK recipe)

I chose a flat 2-table design because the requirements don't need day-level metadata. Adding a third table would be over-engineering for the current scope. If future requirements needed day-specific data (notes, themes, etc.), it would be straightforward to migrate.

#### Constraints

* At most one recipe per slot: unique (meal_plan_id, day_of_week, slot, recipe_id)

This is based on an assumption, since it is not specified whether it is possible to have more than one recipe in the same slot. For now, I have assumed that it is not possible, but it is an idea that can be reevaluated. 


#### Implementation

I added the respective DB models:
* `app/models/meal_plan.py`
* `app/models/meal_plan_item.py`

In addition, I also took into account the relationships between the models: 
* MealPlan → user (A mealPlan belongs to a user; a user can have multiple mealPlans)
* MealPlan → items (A MealPlanItem belongs to a MealPlan; a mealPlan can have several items)
* MealPlanItem → recipe (A MealPlanItem has a recipe)

Note for indexing: The Meal Planning feature is read heavy for meal_plan_items table. The most common requests (“get meal plan” and “generate shopping list”) first filter items by meal_plan_id, then join to recipes (and recipe ingredients). To avoid full table scans, I added indexes on the columns most frequently used. In particular, meal_plan_items.meal_plan_id is indexed because almost every read path starts by retrieving all items for a given meal plan. I also indexed recipe_id to speed joins to the recipes table and support potential future queries such as finding all meal plan usages of a recipe.

#### Alembic migration
I added the created models into the file `app/models/__init__.py`, so Alembic can "sees" them and create the adecuate migrations.