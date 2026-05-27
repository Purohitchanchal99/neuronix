"""
Fix the master_mapping.json to use correct OpenStax direct PDF links
"""

import json
from pathlib import Path

# Define correct OpenStax direct PDF URLs
OPENSTACK_URLS = {
    "psychology": "https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf",
    "biology": "https://assets.openstax.org/oscms-prodcms/media/documents/Biology2e-WEB.pdf",
    "statistics": "https://openstax.org/books/introductory-statistics"  # Web version for now
}

# Path to mapping file
mapping_file = Path(__file__).parent / "data" / "master_mapping.json"

# Load the mapping
with open(mapping_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Statistics for fixing
fixes = {
    "psychology": 0,
    "biology": 0,
    "statistics": 0,
    "other_archive": 0
}

# Iterate through all countries and subjects
for country_code, country_data in data.get('countries', {}).items():
    country_name = country_data.get('full_name', country_code)
    subjects = country_data.get('subjects', {})
    
    for subject_id, subject_data in subjects.items():
        subject_name = subject_data.get('subject_name', subject_id)
        free_alt = subject_data.get('free_alternative', '')
        
        # Check if it's an OpenStax archive URL (the broken ones) and replace with correct one
        if 'openstax.org/apps/archive' in free_alt:
            # Determine which book based on the hash
            if '2e44e844e6d1c0674b1e6e63e3d8da21fcaa0e5d' in free_alt:  # Psychology
                subject_data['free_alternative'] = OPENSTACK_URLS["psychology"]
                fixes["psychology"] += 1
            elif 'a5832c47ab5cf09b6dd19d2c87bf1e0301a4b5e3' in free_alt:  # Biology
                subject_data['free_alternative'] = OPENSTACK_URLS["biology"]
                fixes["biology"] += 1
            elif '59a36a12beda22e37ffd2ad77c31eae3f8a9aaec' in free_alt:  # Statistics
                subject_data['free_alternative'] = OPENSTACK_URLS["statistics"]
                fixes["statistics"] += 1
        elif free_alt.startswith('https://archive.org'):
            fixes["other_archive"] += 1

# Save the fixed mapping
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Master mapping fixed with correct OpenStax PDF URLs:")
print(f"  - Psychology entries fixed: {fixes['psychology']}")
print(f"  - Biology entries fixed: {fixes['biology']}")
print(f"  - Statistics entries: {fixes['statistics']}")
print(f"  - Archive.org entries (left unchanged): {fixes['other_archive']}")
print("\nCorrect URLs now being used:")
print(f"  - Psychology: {OPENSTACK_URLS['psychology']}")
print(f"  - Biology: {OPENSTACK_URLS['biology']}")
print(f"  - Statistics: {OPENSTACK_URLS['statistics']}")
