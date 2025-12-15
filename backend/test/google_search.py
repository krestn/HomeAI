from app.services.google_places import find_local_appraisers

results = find_local_appraisers("Bolingbrook, IL")

for r in results:
    print(r)
