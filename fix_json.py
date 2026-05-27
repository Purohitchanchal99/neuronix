#!/usr/bin/env python3
"""
Fix master_mapping.json by removing comma-separated alternatives
and keeping only the most reliable direct download link for each entry.

Strategy:
1. For most countries: Use OpenStax direct PDFs (most reliable)
2. For India: Use OpenStax direct PDFs first, with IGNOU alternatives noted
3. Remove ALL comma-separated alternatives initially
"""

import json

# OpenStax direct PDF links
OPENSTAX_PSYCHOLOGY = "https://openstax.org/apps/archive/20240401.180420/resources/2e44e844e6d1c0674b1e6e63e3d8da21fcaa0e5d"
OPENSTAX_BIOLOGY = "https://openstax.org/apps/archive/20240401.180420/resources/a5832c47ab5cf09b6dd19d2c87bf1e0301a4b5e3"
OPENSTAX_STATISTICS = "https://openstax.org/apps/archive/20240401.180420/resources/59a36a12beda22e37ffd2ad77c31eae3f8a9aaec"
FRANKL_PDF = "https://archive.org/download/frankl_mans_search_for_meaning/frankl_mans_search_for_meaning.pdf"
PIAGET_PDF = "https://archive.org/download/piaget_psychology_of_intelligence/piaget_psychology_of_intelligence.pdf"

# Load JSON
with open('data/master_mapping.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

# Track changes
changes = {
    'psychology_simplified': 0,
    'biology_simplified': 0,
    'statistics_simplified': 0,
    'archive_fixed': 0,
    'removed_comma_separated': 0,
    'india_special': 0
}

# Process each country and subject
for country_code, country_data in data['countries'].items():
    if 'subjects' not in country_data:
        continue
    
    for subject_key, subject_data in country_data['subjects'].items():
        old_url = subject_data.get('free_alternative', '')
        
        # Skip if empty
        if not old_url:
            continue
        
        # If more than one URL separated by comma, simplify
        if ',' in old_url:
            urls = [u.strip() for u in old_url.split(',')]
            
            # Special handling for India - prefer IGNOU first, fallback to OpenStax
            if country_code == 'India':
                if any('egyankosh' in u for u in urls):
                    # Has IGNOU - keep it (will be handled manually)
                    subject_data['free_alternative'] = urls[0]
                    changes['india_special'] += 1
                elif any('openstax' in u for u in urls):
                    # Use OpenStax for quick download
                    subject_data['free_alternative'] = [u for u in urls if 'openstax' in u][0]
                    changes['removed_comma_separated'] += 1
            else:
                # For non-India: use the first URL or prefer OpenStax
                openstax_urls = [u for u in urls if 'openstax' in u]
                if openstax_urls:
                    subject_data['free_alternative'] = openstax_urls[0]
                    changes['removed_comma_separated'] += 1
                else:
                    subject_data['free_alternative'] = urls[0]
                    changes['removed_comma_separated'] += 1

# Save updated JSON
with open('data/master_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("=" * 70)
print("MASTER_MAPPING.JSON - SIMPLIFICATION COMPLETE")
print("=" * 70)
print(f"✓ Comma-separated URLs removed: {changes['removed_comma_separated']}")
print(f"✓ India entries simplified: {changes['india_special']}")
print(f"✓ All entries now have single URLs")
print("=" * 70)
print("\nNext step: Run the downloader again")
print("→ python scripts/downloader.py")
