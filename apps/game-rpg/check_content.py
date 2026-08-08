import sim_systems
from game_data import expand_game
expand_game()

print('=== SCENE OBJECTS ===')
for loc, objs in sim_systems.SCENE_OBJECTS.items():
    if objs:
        print(f'  {loc}: {len(objs)} objects')
        for o in objs[:3]:
            name = o.get("name", o.get("id"))
            otype = o.get("type", "?")
            print(f'    - {name}: {otype}')

print()
print('=== REAL ESTATE ===')
for k, v in sim_systems.REAL_ESTATE.items():
    print(f'  {k}: {v["type"]} - {v["price"]}G - {v["functions"]} - max Lv.{v.get("max_level",1)}')

print()
print('=== VEHICLES ===')
for k, v in sim_systems.VEHICLES.items():
    print(f'  {k}: {v}')

print()
print('=== QUESTS ===')
for q in sim_systems.QUESTS:
    q_type = q.get("type", q.get("quest_type", "unknown"))
    print(f'  {q["id"]}: {q["title"]} ({q_type}) - {q.get("location", "any")}')

print()
print('=== ENEMY DISTRIBUTION ===')
for loc, enemies in sim_systems.LOCATION_ENEMIES.items():
    print(f'  {loc}: {enemies}')

print()
print('=== RECIPES ===')
for r in sim_systems.RECIPES:
    print(f'  {r["recipe_id"]}: {r["name"]} ({r["category"]}) - ingredients: {r["ingredients"]}')