"""
Patch master_mapping.json with direct PDF links for failed/manual review entries.

Replacements:
- Purdue OWL → MIT OCW Research Paper Guide or LibreTexts equivalents
- Noba Project → Find direct download PDFs or use alternative psychology guides
- OpenStax Statistics → Direct PDF link
"""

import json
from pathlib import Path

mapping_file = Path(__file__).parent / "data" / "master_mapping.json"

# Load mapping
with open(mapping_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Define replacement URLs
REPLACEMENTS = {
    # Purdue OWL → MIT OCW and LibreTexts alternatives
    "https://owl.purdue.edu/site_sharing/owl_in_the_schools/files/owl_research_paper_guide_handout.pdf": 
        "https://ocw.mit.edu/courses/21w-781-advanced-research-writing-spring-2017/",  # MIT OCW Writing
    
    # Noba Project (cognitive/development) → Alternative psychology resources
    "https://nobaproject.com/textbooks/cognitive-psychology-a-student-friendly-introduction":
        "https://pressbooks.pub/apobiology/",  # Open psychology textbook
    
    "https://nobaproject.com/textbooks/human-lifespan-development":
        "https://opentextbc.ca/psych/chapter/human-development/",  # BC Open Textbook
    
    "https://nobaproject.com/textbooks/the-history-of-psychology":
        "https://pressbooks.bccampus.ca/psychologyhistory/",  # History of Psychology textbook
    
    # OpenStax Statistics → Direct PDF
    "https://openstax.org/books/introductory-statistics":
        "https://assets.openstax.org/oscms-prodcms/media/documents/IntroductoryStatistics-WEB.pdf"
}

# Count changes
changes = 0

# Iterate through all countries and subjects
for country_code, country_data in data.get('countries', {}).items():
    subjects = country_data.get('subjects', {})
    
    for subject_id, subject_data in subjects.items():
        url = subject_data.get('free_alternative', '')
        
        # Check if this URL needs replacement
        for old_url, new_url in REPLACEMENTS.items():
            if old_url in url or url == old_url:
                subject_data['free_alternative'] = new_url
                changes += 1
                print(f"✓ {country_data.get('full_name', country_code)} - {subject_data.get('subject_name', subject_id)}")
                print(f"  {old_url[:60]}... → {new_url[:60]}...")
                break

# Save patched mapping
with open(mapping_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Patched {changes} entries in master_mapping.json")
print("\nNote: Some URLs are web pages (MIT OCW, BC Open Textbooks).")
print("These entries will be flagged for manual PDF extraction or web access.")
