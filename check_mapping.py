import json

with open('data/master_mapping.json', 'r') as f:
    mapping = json.load(f)

count_status_0 = 0
count_status_1 = 0

print("=" * 80)
print("FREE RESOURCES (Status 0) in master_mapping.json")
print("=" * 80)

for country_code, country_data in mapping.get('countries', {}).items():
    for subject_code, subject_data in country_data.get('subjects', {}).items():
        if subject_data.get('status') == 0:
            count_status_0 += 1
            free_alt = subject_data.get('free_alternative', 'No link')
            country_name = country_data.get('full_name', country_code)
            subject_name = subject_data.get('subject_name', subject_code)
            print(f"{country_name:20} | {subject_name:30} | {free_alt}")
        else:
            count_status_1 += 1

print("\n" + "=" * 80)
print(f"Status 0 (Free): {count_status_0} items")
print(f"Status 1 (Paid): {count_status_1} items")
print("=" * 80)

if count_status_0 == 0:
    print("\n! WARNING: No Status 0 (free) resources found in mapping")
    print("  The downloader only processes Status 0 items")
    print("  Most items in the default mapping are Status 1 (paid with alternatives)")
    print("\n  To test the system, you need to either:")
    print("    1. Add some Status 0 items to master_mapping.json")
    print("    2. Create sample PDFs in /docs/India/ folder manually")
