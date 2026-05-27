"""
Fix remaining failed entries in master_mapping.json with alternative sources
"""

import json
from pathlib import Path

# Alternative sources for failed entries
ALTERNATIVE_SOURCES = {
    # Frankl - "Man's Search for Meaning" alternatives
    "frankl": "https://openlibrary.org/books/OL400002M/Man_s_search_for_meaning",
    
    # Piaget - "The Psychology of Intelligence" alternatives  
    "piaget": "https://openlibrary.org/books/OL5926397M/The_Psychology_of_Intelligence",
    
    # Purdue OWL - Direct to research guide PDF
    "purdue_owl": "https://owl.purdue.edu/site_sharing/owl_in_the_schools/files/owl_research_paper_guide_handout.pdf"
}

# Path to mapping file
mapping_file = Path(__file__).parent / "data" / "master_mapping.json"

# Load the mapping
with open(mapping_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

fixes = {
    "frankl": 0,
    "piaget": 0,
    "purdue": 0
}

# Iterate through all countries and subjects
for country_code, country_data in data.get('countries', {}).items():
    country_name = country_data.get('full_name', country_code)
    subjects = country_data.get('subjects', {})
    
    for subject_id, subject_data in subjects.items():
        subject_name = subject_data.get('subject_name', subject_id)
        free_alt = subject_data.get('free_alternative', '')
        
        # Fix Frankl entries
        if 'frankl_mans_search_for_meaning' in free_alt.lower():
            subject_data['free_alternative'] = ALTERNATIVE_SOURCES["frankl"]
            fixes["frankl"] += 1
            print(f"  ✓ {country_name} - {subject_name}: Frankl → OpenLibrary")
        
        # Fix Piaget entries
        elif 'piaget_psychology_of_intelligence' in free_alt.lower():
            subject_data['free_alternative'] = ALTERNATIVE_SOURCES["piaget"]
            fixes["piaget"] += 1
            print(f"  ✓ {country_name} - {subject_name}: Piaget → OpenLibrary")
        
        # Fix Purdue OWL entries
        elif 'owl.purdue.edu' in free_alt.lower() and 'research_and_citation' in free_alt.lower():
            subject_data['free_alternative'] = ALTERNATIVE_SOURCES["purdue_owl"]
            fixes["purdue"] += 1
            print(f"  ✓ {country_name} - {subject_name}: Purdue OWL → PDF Guide")

# Save the fixed mapping
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n" + "="*70)
print("FAILED ENTRIES PATCHED WITH ALTERNATIVES:")
print("="*70)
print(f"Frankl entries fixed:    {fixes['frankl']}")
print(f"Piaget entries fixed:    {fixes['piaget']}")
print(f"Purdue OWL entries fixed: {fixes['purdue']}")
print(f"\nTotal patches applied:   {sum(fixes.values())}")
print("\nAlternatives used:")
print(f"  - Frankl: {ALTERNATIVE_SOURCES['frankl']}")
print(f"  - Piaget: {ALTERNATIVE_SOURCES['piaget']}")
print(f"  - Purdue: {ALTERNATIVE_SOURCES['purdue_owl']}")
print("\nReady to re-run downloader!")
