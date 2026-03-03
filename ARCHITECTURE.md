# ARCHITECTURE — Meal Planning Case Study
---
## Data model decisions

### Tables
I decided to implement to new tables:

* `meal_plan`: stores the meal plan metadata and ownership
    - id (PK)
    - user_id (FK user), owner of the meal plan
    - name, plan name
    - created_at
    - updated_at

* `meal_plan_items`: stores the assignments of recipes into days and slots
    - id (PK)
    - meal_plan_id (FK meal_plan), meal plan to which an item belongs
    - day_of_week, `0..6` where 0=Monday and 6=Sunday
    - slot, one of `breakfast|lunch|dinner` (this can be extended)
    - recipe_id (FK recipe)

I chose a flat 2-table design because the requirements don't need day-level metadata. This keeps the persistence model simple while supporting the required functionality: weekly plan, multiple meal slots per day, and shopping-list generation across selected recipes. An alternative design would introduce a meal_plan_days intermediate table, making each day a first-class entity; adding a third table would be over-engineering for the current scope. If future requirements needed day-specific data (notes, themes, etc.), it would be straightforward to migrate.

### Relationships
- A `User` has many `MealPlans`
- A `MealPlan` has many `MealPlanItems`
- A `MealPlanItem` references one `Recipe`

### Constraints

- `day_of_week` field (`0..6`) has weekly coverage for meal plans. The API validates the range at the schema level and treats these values consistently throughout the application.
- `slot` is represented as a string (`breakfast|lunch|dinner`). This makes the API self-describing.
- Uniqueness is enforced via a database constraint:
  - `UNIQUE(meal_plan_id, day_of_week, slot)`
  - This allows one recipe per slot, a slot can only be assigned one recipe per day.

### Ondelete

`meal_plan_items` uses `ondelete="CASCADE"` on the `meal_plan_id` foreign key, so deleting a meal plan automatically removes all its items.
`recipe_id` on `meal_plan_items` uses `ondelete="RESTRICT"`, which prevents a recipe from being deleted while it is referenced by an active meal plan. This avoids silent data loss and forces the caller to handle the dependency explicitly.

---

## Shopping list aggregation

### Goal
The `/meal-plans/{id}/shopping-list` endpoint generates a shopping list by collecting ingredients from all recipes that appear in a meal plan, taking into account duplicates.

### Steps
1. Load the full meal plan with all items, their recipes, and each recipe's ingredients in a single query using eager loading (`selectinload chains`)
   - MealPlan → items → recipe → ingredients
2. Iterate all ingredients across all assigned recipes.
3. Aggregate with a dictionary keyed by `(ingredient_name, unit)` to group matching ingredients and sum quantities.
4. If a quantity is `None`, the ingredient is included in the list without a numeric quantity, so it is not silently dropped. Return the list

### Aggregation key and normalization
Aggregation uses a normalized key to avoid treating minor formatting differences as separate ingredients:
- `ingredient_name = ingredient.name.strip().lower()`
- `unit = ingredient.unit.strip().lower()` 

This groups `"Egg"` and `"egg"` together and avoids duplicates caused by accidental whitespace.

### Handling missing quantities and units
The existing `Ingredient` model allows `quantity` and `unit` to be optional.
To keep the shopping list “clean” and meaningful:
- Ingredients with `quantity is None` are not skipped, but the sum does not count.
- Units may be `None`. Items with `unit=None` are aggregated separately from items with a unit.


### Edge cases
- **Same ingredient used across multiple recipes**: summed by `(name, unit)`.
- **Same ingredient, different units**: treated as separate items since the units differs. Unit normalization can be a future improvement.
- **Ingredient with no quantity**: No silently dropped, included in the list with no quantity.
- **Different casing / whitespace**: normalized (strip and lower case) to avoid duplicates.

---

## Scaling considerations
The current architecture is appropriate for development and low-traffic use. If the API served 10,000 concurrent users, the primary concerns would be database load, connection management, and request latency.

### Database
- Majority of traffic (GET requests) can be routed to read replicas, reserving the primary for writes, so allowing read replicas would be essential

- Use efficient eager-loading (`selectinload`) to avoid N+1 queries in shopping list generation.
- Ensure all foreign key columns used in filter querys are indexed (`meal_plans.user_id`, `meal_plan_items.meal_plan_id`, `meal_plan_items.recipe_id`). This is already applied in the current model.
- Considerations in caching the shopping list result for a meal plan if meal plans are read frequently but updated rarely. the shopping list endpoint performs a deep join chain, under high load this query should be profiled

### Caching
The shopping list for a meal plan is expensive to compute and changes only when the plan is updated. A short cache can be applied to it. Recipe ingredient data changes infrequently and could also be cached at the recipe level. In this way, the query can be optimize using only cache strategies.

### Connection pooling
- Tweak SQLAlchemy async initialization pool size and overflow to match higher concurrency.
- Add `pool_pre_ping=True` to avoid failures from stale connections.

### Horizontal scaling
- Multiple instances can run behind a load balancer without coordination, this would help with high concurrency. Authentication uses JWT, which is stateless and scales without a shared session store.


## Production readiness

Before deploying to production, I would add or adjust the following:

### Schema management
- Use Alembic migrations as the single source of truth for schema changes. Limit database access for developers with this.
- Migrations should be run as a separate step in the deployment pipeline before deploying any new version.

### Security
- Load secrets (DB URL, JWT secret) from required environment variables or a secret manager, delete all hardcoded secret deaults.
- Restrict CORS origins (avoid using `allow_origins=["*"]` in production).
- Protect authentication endpoints from brute-force attacks with a rate limiting


### Reliability 
- Map expected database constraint violations (like unique constraint violations) to specific HTTP errors and rollback the failed transaction.
- Add health endpoints for deployment platforms.
- Make sure that requests that are still being processed are completed before the process exits.

### Observability

* Make use of structured JSON logs so that log aggregation tools (like Datadog) can parse and query them, and devs can retrieve information about possible errors.
* Expose a metrics endpoint covering request counts, latency percentiles, and error rates.


### CI/CD
- Add CI pipeline steps:
  - `pytest`
  - linting or formatting
- Run migrations automatically in deployment pipeline (using `alembic upgrade head`).
- Docker Compose setup file should closely mirror the production environment to catch configuration issues early.
