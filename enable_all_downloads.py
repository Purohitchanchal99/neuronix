"""
Enable all entries with free_alternative URLs for downloading
"""

import json
from pathlib import Path

mapping_file = Path(__file__).parent / "data" / "master_mapping.json"

with open(mapping_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

updated_count = 0
for country_code, country_data in data.get('countries', {}).items():
    subjects = country_data.get('subjects', {})
    for subject_id, subject_data in subjects.items():
        free_alt = subject_data.get('free_alternative', '')
        # If it has a free_alternative URL, set status to 0 so it can be downloaded
        if free_alt and subject_data.get('status', 1) != 0:
            subject_data['status'] = 0
            updated_count += 1

with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Updated {updated_count} entries to status 0 for downloading")
print("Ready to run downloader on all countries!")
