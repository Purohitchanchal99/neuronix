#!/usr/bin/env python3
"""
Replace problematic URLs in master_mapping.json with working alternatives:
1. India IGNOU → OpenStax Psychology direct PDF
2. Archive.org (Frankl, Piaget) → Alternative sources or skip
"""

import json

# Direct PDF links that work
OPENSTAX_PSYCHOLOGY = "https://openstax.org/apps/archive/20240401.180420/resources/2e44e844e6d1c0674b1e6e63e3d8da21fcaa0e5d"

# Load JSON
with open('data/master_mapping.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

changes = 0

# Fix India entries: replace IGNOU with OpenStax
if 'India' in data['countries']:
    for subject_key, subject_data in data['countries']['India']['subjects'].items():
        url = subject_data.get('free_alternative', '')
        
        # If it's IGNOU portal URL, replace with OpenStax PDF
        if 'egyankosh.ac.in' in url and '/' not in url.replace('://', ''):
            # This is just the portal - replace with direct PDF
            subject_data['free_alternative'] = OPENSTAX_PSYCHOLOGY
            changes += 1
            print(f"  ✓ India - {subject_data['subject_name']}: {url} → OpenStax PDF")

# Fix Archive.org entries: skip them (can't be auto-downloaded)
# We'll document them but not force downloads
for country_code, country_data in data['countries'].items():
    if 'subjects' not in country_data:
        continue
    
    for subject_key, subject_data in country_data['subjects'].items():
        url = subject_data.get('free_alternative', '')
        
        if 'archive.org/download' in url:
            # Archive.org PDFs can't be auto-downloaded reliably
            # Keep the URL but mark it with a note
            print(f"  ℹ {country_code} - {subject_data['subject_name']}: Archive.org (manual download needed)")

# Save updated JSON
with open('data/master_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 70)
print(f"✓ Updated India entries: {changes}")
print("=" * 70)
print("\nReady for re-running downloader!")
