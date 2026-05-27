#!/usr/bin/env python3
"""
Validate free textbook URLs before patching
Test accessibility and direct PDF availability
"""

import requests
from pathlib import Path

# URLs to test - grouped by source
SOURCES_TO_TEST = {
    "OpenStax": [
        ("Psychology 2e", "https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf"),
        ("Biology 2e", "https://assets.openstax.org/oscms-prodcms/media/documents/Biology2e-WEB.pdf"),
        ("Statistics", "https://assets.openstax.org/oscms-prodcms/media/documents/IntroductoryStatistics-OP.pdf"),
    ],
    "LibreTexts": [
        ("Psychology", "https://chem.libretexts.org/Bookshelves/Social_and_Behavioral_Sciences/"),
        ("Statistics", "https://stats.libretexts.org/"),
    ],
    "OpenIntro": [
        ("Statistics", "https://www.openintro.org/data/openintro-statistics.pdf"),
    ],
    "UMN OpenTextbooks": [
        ("Psychology Foundation", "https://open.umn.edu/opentextbooks/formats/2166"),
    ],
    "BCcampus OpenEd": [
        ("Abnormal Psychology", "https://pressbooks.bccampus.ca/abnormalpsychology2019/"),
        ("Social Psychology", "https://pressbooks.bccampus.ca/socialpsychology/"),
        ("Psychology History", "https://pressbooks.bccampus.ca/psychologyhistory/"),
    ],
    "OpenTextBook Library": [
        ("OAPEN Psychology", "https://www.oapen.org/handle/20.500.12657/49391"),
    ],
    "Archive.org Public Domain": [
        ("Frankl - Man's Search", "https://archive.org/download/MansSe/MansSe_djvu.txt"),
        ("Piaget - Intelligence", "https://archive.org/download/PsychologyOfIntelligence/PsychologyOfIntelligence_djvu.txt"),
        ("Freud - Dreams", "https://archive.org/download/TheInterpretationOfDreams/the-interpretation-of-dreams_djvu.txt"),
    ],
    "IGNOU": [
        ("NCERT Biology", "https://ncert.nic.in/textbook.php?keps1=sc"),
        ("IGNOU Psychology", "https://egyankosh.ac.in/"),
    ],
    "MIT OCW": [
        ("Research Writing", "https://ocw.mit.edu/courses/21w-781-advanced-research-writing-spring-2017/"),
    ]
}

def test_url(url, timeout=5):
    """Test if URL is accessible"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code < 400
    except:
        try:
            response = requests.get(url, timeout=timeout, stream=True)
            return response.status_code < 400
        except:
            return False

def main():
    print("=" * 80)
    print("VALIDATING FREE TEXTBOOK SOURCES")
    print("=" * 80)
    print()
    
    working_count = 0
    total_count = 0
    
    for source_name, urls in SOURCES_TO_TEST.items():
        print(f"📚 {source_name}")
        print("-" * 80)
        
        for book_name, url in urls:
            total_count += 1
            try:
                is_working = test_url(url)
                status = "✅ WORKS" if is_working else "❌ BLOCKED/404"
                
                if is_working:
                    working_count += 1
                    print(f"  ✓ {book_name}: {status}")
                    print(f"    URL: {url}")
                else:
                    print(f"  ✗ {book_name}: {status}")
                    print(f"    URL: {url}")
                    
            except Exception as e:
                print(f"  ✗ {book_name}: ERROR - {str(e)[:50]}")
        
        print()
    
    print("=" * 80)
    print(f"SUMMARY: {working_count}/{total_count} sources verified")
    print(f"Success rate: {(working_count/total_count)*100:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
