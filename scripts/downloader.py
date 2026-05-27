"""
Neuronix Free Medical Textbook Downloader
==========================================
This script reads the master_mapping.json file and attempts to download
free alternative textbooks for various countries and subjects.

Features:
- Iterates through all countries and subjects
- Identifies free alternatives (Status 0)
- Downloads PDFs and saves them organized by country
- Logs problematic links for manual review
- Uses Requests and BeautifulSoup for robust downloading
"""

import json
import os
import shutil
import requests
import logging
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup # pyright: ignore[reportMissingImports]
from datetime import datetime
import time

# Configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
SCRIPTS_DIR = BASE_DIR / "scripts"
MAPPING_FILE = DATA_DIR / "master_mapping.json"
LOG_FILE = SCRIPTS_DIR / "download_log.txt"
MANUAL_REVIEW_FILE = SCRIPTS_DIR / "manual_review_links.txt"

# Download settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
CHUNK_SIZE = 8192
USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TextbookDownloader:
    """Main class for downloading free textbooks from master_mapping.json"""
    
    def __init__(self):
        self.mapping_data = None
        self.downloaded_files = []
        self.failed_downloads = []
        self.manual_review_links = []
        self.session = requests.Session()
        self.session.headers.update(USER_AGENT)
        
    def load_mapping(self):
        """Load the master_mapping.json file"""
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                self.mapping_data = json.load(f)
            logger.info(f"Successfully loaded mapping file from {MAPPING_FILE}")
            return True
        except FileNotFoundError:
            logger.error(f"Mapping file not found at {MAPPING_FILE}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON file: {e}")
            return False
    
    def extract_free_alternatives(self):
        """Extract all free alternatives (Status 0) from mapping"""
        free_items = []
        
        if not self.mapping_data or 'countries' not in self.mapping_data:
            logger.error("Invalid mapping data structure")
            return free_items
        
        countries = self.mapping_data['countries']
        
        for country_code, country_data in countries.items():
            country_name = country_data.get('full_name', country_code)
            subjects = country_data.get('subjects', {})
            
            for subject_id, subject_data in subjects.items():
                status = subject_data.get('status', 1)
                
                # Only process free alternatives (status 0)
                if status == 0:
                    free_items.append({
                        'country': country_name,
                        'country_code': country_code,
                        'subject': subject_data.get('subject_name', subject_id),
                        'subject_id': subject_id,
                        'free_alternative': subject_data.get('free_alternative', ''),
                        'paid_book': subject_data.get('paid_book', '')
                    })
        
        logger.info(f"Found {len(free_items)} free alternatives to process")
        return free_items
    
    def is_direct_pdf_link(self, url):
        """Check if URL is a direct PDF link"""
        if not url:
            return False
        
        url_lower = url.lower()
        return url_lower.endswith('.pdf') or 'pdf' in url_lower[:50]
    
    def is_valid_url(self, url):
        """Check if string is a valid URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def parse_free_alternatives(self, alternatives_text):
        """
        Parse free alternatives text to extract URLs and local file paths
        Text can be like "OpenStax Biology 2e" or contain embedded URLs or file paths
        """
        urls = []
        text_parts = []
        
        if not alternatives_text:
            return urls, text_parts
        
        # Split by comma and process each part
        parts = [p.strip() for p in alternatives_text.split(',')]
        
        for part in parts:
            # Check if it's a local file path first
            if os.path.isfile(part):
                urls.append(part)  # Add local files to urls list for processing
            elif self.is_valid_url(part):
                urls.append(part)
            else:
                text_parts.append(part)
        
        return urls, text_parts
    
    def create_country_directory(self, country_name):
        """Create a directory for the country in /docs"""
        country_dir = DOCS_DIR / country_name.replace(' ', '_')
        country_dir.mkdir(parents=True, exist_ok=True)
        return country_dir
    
    def sanitize_filename(self, filename):
        """Sanitize filename to be filesystem-safe"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
    
    def copy_local_file(self, source_path, destination_path):
        """
        Copy a file from local path to destination
        Returns True if successful, False otherwise
        """
        try:
            if not os.path.exists(source_path):
                logger.warning(f"Source file not found: {source_path}")
                return False
            
            logger.info(f"Copying from cache: {source_path}")
            shutil.copy2(source_path, destination_path)
            
            file_size = os.path.getsize(destination_path)
            logger.info(f"Successfully copied: {destination_path} ({file_size} bytes)")
            self.downloaded_files.append(str(destination_path))
            return True
        except Exception as e:
            logger.warning(f"Error copying local file: {e}")
            return False
    
    def download_file(self, url, destination_path, max_retries=MAX_RETRIES):
        """
        Download a file from URL and save to destination
        Returns True if successful, False otherwise
        """
        if not self.is_valid_url(url):
            logger.debug(f"Invalid URL format: {url}")
            return False
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading (attempt {attempt + 1}/{max_retries}): {url}")
                
                response = self.session.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                    stream=True
                )
                response.raise_for_status()
                
                # Check if response is actually a PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
                    logger.warning(f"Response doesn't appear to be PDF: {url}")
                    return False
                
                # Write file
                with open(destination_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                
                file_size = os.path.getsize(destination_path)
                logger.info(f"Successfully downloaded: {destination_path} ({file_size} bytes)")
                self.downloaded_files.append(str(destination_path))
                return True
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}: {url}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error on attempt {attempt + 1}: {url}")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.warning(f"Error on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retry
        
        self.failed_downloads.append(url)
        return False
    
    def process_alternative(self, item):
        """Process a single free alternative item"""
        country = item['country']
        subject = item['subject']
        alternatives = item['free_alternative']
        
        logger.info(f"\nProcessing: {country} - {subject}")
        logger.info(f"Alternatives: {alternatives}")
        
        # Create country directory
        country_dir = self.create_country_directory(country)
        
        # Parse alternatives
        urls, text_parts = self.parse_free_alternatives(alternatives)
        
        # Store text parts for manual review
        if text_parts:
            for text_part in text_parts:
                if text_part and not any(x in text_part.lower() for x in ['open', 'simply', 'ignou', 'khan', 'libre']):
                    # Only flag if it looks like it might need manual review
                    pass
        
        # Attempt to download/copy direct PDF URLs or local files
        for url in urls:
            # Check if it's a local file path first
            if os.path.isfile(url):
                # It's a local file - copy it instead of downloading
                filename = self.sanitize_filename(f"{subject}_{os.path.basename(url)}")
                destination = country_dir / filename
                
                if not self.copy_local_file(url, destination):
                    # Log for manual review
                    self.manual_review_links.append({
                        'country': country,
                        'subject': subject,
                        'url': url,
                        'reason': 'Failed to copy from cache'
                    })
            elif self.is_direct_pdf_link(url):
                # Generate filename from subject and URL
                filename = self.sanitize_filename(f"{subject}_{urlparse(url).path.split('/')[-1]}")
                if not filename.endswith('.pdf'):
                    filename += '.pdf'
                
                destination = country_dir / filename
                
                if not self.download_file(url, destination):
                    # Log for manual review
                    self.manual_review_links.append({
                        'country': country,
                        'subject': subject,
                        'url': url,
                        'reason': 'Failed to download'
                    })
            else:
                # Non-direct PDF URL - log for manual review
                self.manual_review_links.append({
                    'country': country,
                    'subject': subject,
                    'url': url,
                    'reason': 'Not a direct PDF link (may be webpage or resource portal)'
                })
                logger.info(f"Flagged for manual review: {url}")
    
    def generate_manual_review_report(self):
        """Generate a report of links that need manual review"""
        if not self.manual_review_links:
            logger.info("No links require manual review")
            return
        
        try:
            with open(MANUAL_REVIEW_FILE, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("NEURONIX - MANUAL REVIEW REQUIRED\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Total items requiring manual review: {len(self.manual_review_links)}\n\n")
                
                # Group by country
                by_country = {}
                for item in self.manual_review_links:
                    country = item['country']
                    if country not in by_country:
                        by_country[country] = []
                    by_country[country].append(item)
                
                for country in sorted(by_country.keys()):
                    f.write(f"\n{'='*80}\n")
                    f.write(f"COUNTRY: {country}\n")
                    f.write(f"{'='*80}\n")
                    
                    for idx, item in enumerate(by_country[country], 1):
                        f.write(f"\n{idx}. Subject: {item['subject']}\n")
                        f.write(f"   Reason: {item['reason']}\n")
                        f.write(f"   URL: {item['url']}\n")
                        f.write(f"   Action: Please visit the URL and download manually\n")
                        f.write("-" * 80 + "\n")
            
            logger.info(f"Manual review report saved to {MANUAL_REVIEW_FILE}")
        except Exception as e:
            logger.error(f"Error generating manual review report: {e}")
    
    def generate_summary_report(self):
        """Generate a summary of the download process"""
        summary = f"""
{'='*80}
NEURONIX DOWNLOADER - SUMMARY REPORT
{'='*80}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

STATISTICS:
-----------
Total Files Downloaded: {len(self.downloaded_files)}
Failed Downloads: {len(self.failed_downloads)}
Items for Manual Review: {len(self.manual_review_links)}

DOWNLOADED FILES:
-----------------
"""
        if self.downloaded_files:
            for file_path in self.downloaded_files:
                summary += f"\n  ✓ {file_path}"
        else:
            summary += "\n  (No files downloaded)"
        
        summary += f"""

FAILED DOWNLOADS:
-----------------
"""
        if self.failed_downloads:
            for url in self.failed_downloads:
                summary += f"\n  ✗ {url}"
        else:
            summary += "\n  (No failures)"
        
        summary += f"""

MANUAL REVIEW ITEMS:
--------------------
"""
        if self.manual_review_links:
            summary += f"\n  See {MANUAL_REVIEW_FILE} for details"
        else:
            summary += "\n  (No items require manual review)"
        
        summary += f"""

NOTES:
------
- Downloaded files are organized by country in the /docs folder
- Manual review file: {MANUAL_REVIEW_FILE}
- Log file: {LOG_FILE}
- Review the manual review file to download remaining resources

{'='*80}
"""
        logger.info(summary)
        
        # Also save summary to file
        summary_file = SCRIPTS_DIR / "download_summary.txt"
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            logger.info(f"Summary report saved to {summary_file}")
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
    
    def run(self):
        """Main execution method"""
        logger.info("=" * 80)
        logger.info("Starting Neuronix Textbook Downloader")
        logger.info("=" * 80)
        
        # Load mapping
        if not self.load_mapping():
            logger.error("Failed to load mapping file. Exiting.")
            return False
        
        # Create docs directory
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Extract free alternatives
        free_items = self.extract_free_alternatives()
        
        if not free_items:
            logger.warning("No free alternatives found in mapping")
            return False
        
        # Process each item
        for idx, item in enumerate(free_items, 1):
            logger.info(f"\n[{idx}/{len(free_items)}] Processing: {item['country']} - {item['subject']}")
            self.process_alternative(item)
            time.sleep(1)  # Be respectful to servers
        
        # Generate reports
        self.generate_manual_review_report()
        self.generate_summary_report()
        
        logger.info("\n" + "=" * 80)
        logger.info("Download process completed!")
        logger.info("=" * 80)
        
        return True


def main():
    """Entry point"""
    downloader = TextbookDownloader()
    success = downloader.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
