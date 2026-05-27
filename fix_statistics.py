"""
Replace inaccessible OpenStax Statistics PDF with working LibreTexts alternative.
"""

import json
from pathlib import Path

mapping_file = Path(__file__).parent / "data" / "master_mapping.json"

# Load mapping
with open(mapping_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Old and new URLs
old_url = "https://assets.openstax.org/oscms-prodcms/media/documents/IntroductoryStatistics-WEB.pdf"
new_url = "https://stats.libretexts.org/Courses/La_Salle_University"  # LibreTexts Statistics

# Count changes
changes = 0

# Iterate through all countries and subjects
for country_code, country_data in data.get('countries', {}).items():
    subjects = country_data.get('subjects', {})
    
    for subject_id, subject_data in subjects.items():
        url = subject_data.get('free_alternative', '')
        
        if url == old_url:
            subject_data['free_alternative'] = new_url
            changes += 1
            print(f"✓ {country_data.get('full_name', country_code)} - {subject_data.get('subject_name', subject_id)}")

# Save patched mapping
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Replaced {changes} Statistics entries with LibreTexts alternative")
print(f"\nOld: {old_url}")
print(f"New: {new_url}")
print("\nNote: LibreTexts is a web resource. PDF access requires manual download.")
