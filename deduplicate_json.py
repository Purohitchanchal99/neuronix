"""
Deduplicate master_mapping.json by pointing all Psychology/Biology/Statistics entries
to a single cached PDF file instead of downloading repeatedly.
"""

import json
from pathlib import Path

# File paths
mapping_file = Path(__file__).parent / "data" / "master_mapping.json"
docs_dir = Path(__file__).parent / "docs"

# Define local cached files
CACHED_FILES = {
    "psychology": str(docs_dir / "Psychology2e_WEB.pdf"),
    "biology": str(docs_dir / "Biology2e-WEB.pdf"),  # Will be downloaded once
    "statistics": str(docs_dir / "Statistics-WEB.pdf")  # Will be downloaded once
}

# Load mapping
with open(mapping_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track changes
stats = {"psychology": 0, "biology": 0, "statistics": 0}

# Iterate and patch Psychology → local file path
for country_code, country_data in data.get('countries', {}).items():
    subjects = country_data.get('subjects', {})
    
    for subject_id, subject_data in subjects.items():
        url = subject_data.get('free_alternative', '')
        
        # If it's a Psychology OpenStax URL, replace with local path
        if 'Psychology2e_WEB.pdf' in url:
            subject_data['free_alternative'] = CACHED_FILES["psychology"]
            stats["psychology"] += 1
        
        # If it's a Biology OpenStax URL, replace with local path
        elif 'Biology2e-WEB.pdf' in url:
            subject_data['free_alternative'] = CACHED_FILES["biology"]
            stats["biology"] += 1
        
        # If it's a Statistics OpenStax URL, replace with local path
        elif 'Statistics' in url or '59a36a12beda22e37ffd2ad77c31eae3f8a9aaec' in url:
            subject_data['free_alternative'] = CACHED_FILES["statistics"]
            stats["statistics"] += 1

# Save patched mapping
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✓ Successfully patched master_mapping.json for deduplication:")
print(f"  - Psychology entries: {stats['psychology']} updated to local file path")
print(f"  - Biology entries: {stats['biology']} updated to local file path")
print(f"  - Statistics entries: {stats['statistics']} updated to local file path")
print(f"\nLocal cache location: {CACHED_FILES['psychology']}")
print("Note: Downloader will now copy from cache instead of re-downloading!")
