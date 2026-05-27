# Neuronix - AI Healthcare Textbook Distribution System

## Quick Start Guide

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Setup Installation

#### Option 1: Automatic Setup (Recommended)
```bash
# Navigate to the Neuronix project directory
cd NEURO_MENTAL

# Run the setup script
python scripts/setup.py
```

#### Option 2: Manual Installation
```bash
# Install required packages
pip install requests beautifulsoup4
```

### Project Structure

```
NEURO_MENTAL/
├── /docs/                    # Downloaded medical textbooks (organized by country)
├── /backend/                 # FastAPI and LangChain logic
├── /frontend/                # React/Streamlit dashboard
├── /data/                    # Data files
│   └── master_mapping.json   # Countries → Subjects → Free Alternatives mapping
├── /scripts/                 # Python utility scripts
│   ├── setup.py             # Install dependencies
│   └── downloader.py        # Download free textbooks
└── requirements.txt         # Python dependencies list
```

## Downloader Script

### Usage

```bash
# Install dependencies first
python scripts/setup.py

# Run the downloader
python scripts/downloader.py
```

### What It Does

The `downloader.py` script:

1. **Reads** `data/master_mapping.json` containing country/subject/textbook mappings
2. **Identifies** all free alternatives (Status 0 textbooks)
3. **Attempts** to download PDFs from direct links
4. **Organizes** downloaded files by country in `/docs/` folder
5. **Logs** problematic links for manual review

### Output Files

After running the downloader, check:

- **`scripts/download_log.txt`** - Detailed operation log (all activities)
- **`scripts/manual_review_links.txt`** - Links needing manual download
- **`scripts/download_summary.txt`** - High-level summary report
- **`docs/[Country_Name]/`** - Downloaded files organized by country

### Features

✓ Automatic retry logic (3 attempts per URL)
✓ Timeout protection (30-second limit per request)
✓ Filesystem-safe filename handling
✓ URL validation and content-type checking
✓ Proper HTTP headers and user-agent
✓ Organized output with comprehensive logging

## Master Mapping JSON Structure

The `data/master_mapping.json` file contains:

```json
{
  "metadata": {...},
  "countries": {
    "US": {
      "country_code": "🇺🇸",
      "full_name": "United States",
      "subjects": {
        "subject_id": {
          "subject_name": "Subject Name",
          "paid_book": "Paid Textbook Title",
          "status": 1,  // 0 = Free, 1 = Paid
          "free_alternative": "Free textbook/resource name or URL"
        }
      }
    }
  }
}
```

## Key Information

### Countries with Free Textbooks (Status 0)
- **🇮🇳 India** - IGNOU and NCERT PDFs (completely free)
- **🇩🇪 Germany** - Man's Search for Meaning (Public Domain)
- **🇫🇷 France** - Jean Piaget Materials (Public Domain)
- **🇨🇭 Switzerland** - Jean Piaget Materials (Public Domain)

### Universal Free Resources
- **OpenStax Psychology 2e** - Comprehensive psychology textbook
- **Simply Psychology** - UK-based resource
- **IGNOU PDFs** - Indian Government Open University materials
- **Khan Academy** - Statistics courses
- **LibreTexts Psychology** - Collaborative textbook platform
- **Noba Modules** - Open-source psychology modules

## Troubleshooting

### Import Errors (Pylance Warnings)
These are normal development warnings. They disappear once you run:
```bash
python scripts/setup.py
```

### JSON Validation Errors
If `master_mapping.json` shows errors:
```bash
python -c "import json; json.load(open('data/master_mapping.json')); print('✓ Valid')"
```

### Download Failures
Check `scripts/manual_review_links.txt` for:
- Non-direct PDF links (webpages/portals)
- Failed downloads (may need manual download)
- Invalid URLs (typos or outdated links)

### No Downloads
If downloader finds no free alternatives:
1. Verify `data/master_mapping.json` contains Status 0 items
2. Check `scripts/download_log.txt` for errors
3. Ensure internet connection is available

## Next Steps

1. **Run Setup** → `python scripts/setup.py`
2. **Download Textbooks** → `python scripts/downloader.py`
3. **Review Results** → Check `scripts/download_summary.txt`
4. **Manual Review** → For items in `scripts/manual_review_links.txt`

## Support

For issues or contributions:
- Check log files in `/scripts/`
- Review diagnostic information in `.txt` report files
- Verify JSON structure with Python's json module

---

**Last Updated:** April 15, 2026
**Version:** 1.0.0
**Project:** Neuronix - AI Healthcare Startup
