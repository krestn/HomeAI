from app.services.google_places import find_local_services

results = find_local_services("Plumber", "Bolingbrook, IL")

for r in results:
    print(r)
