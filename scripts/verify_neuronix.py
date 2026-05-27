"""
Neuronix System Verification
============================
Verify that the Neuronix system is properly configured and ready to use.

Run: python scripts/verify_neuronix.py
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def check_file_exists(path: Path, name: str) -> bool:
    """Check if a file exists"""
    if path.exists():
        logger.info(f"  ✅ {name}: {path}")
        return True
    else:
        logger.info(f"  ❌ {name}: NOT FOUND ({path})")
        return False


def check_directory_exists(path: Path, name: str, check_pdfs: bool = False) -> bool:
    """Check if directory exists and optionally for PDFs"""
    if path.exists():
        if check_pdfs:
            pdfs = list(path.rglob("*.pdf"))
            count = len(pdfs)
            logger.info(f"  ✅ {name}: {path} ({count} PDFs)")
            return count > 0
        else:
            logger.info(f"  ✅ {name}: {path}")
            return True
    else:
        logger.info(f"  ❌ {name}: NOT FOUND ({path})")
        return False


def check_python_package(package_name: str, import_name: str = None) -> bool:
    """Check if Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        logger.info(f"  ✅ {package_name}")
        return True
    except ImportError:
        logger.info(f"  ❌ {package_name}: NOT INSTALLED")
        return False


def check_env_variable(var_name: str) -> bool:
    """Check if environment variable is set"""
    if var_name in os.environ and os.environ[var_name]:
        logger.info(f"  ✅ {var_name}: Set")
        return True
    else:
        logger.info(f"  ❌ {var_name}: NOT SET")
        return False


def check_database() -> bool:
    """Check if vector database is populated"""
    try:
        from neuronix_query import NeuronixQuerySystem
        
        logger.info("  🔍 Checking ChromaDB...")
        query_system = NeuronixQuerySystem(verbose=False)
        status = query_system.get_db_status()
        
        if status['ready']:
            logger.info(f"    ✅ Database populated: {status['documents_count']:,} documents")
            return True
        else:
            logger.info(f"    ⚠️  Database empty: 0 documents")
            return False
            
    except Exception as e:
        logger.info(f"    ❌ Database check failed: {e}")
        return False


def main():
    """Run verification"""
    logger.info("\n" + "="*80)
    logger.info("🧠 NEURONIX SYSTEM VERIFICATION")
    logger.info("="*80 + "\n")
    
    checks_passed = 0
    checks_failed = 0
    
    # 1. Files
    logger.info("📄 Checking required files...")
    
    files_to_check = [
        (Path(__file__).parent / "neuronix_constants.py", "neuronix_constants.py"),
        (Path(__file__).parent / "neuronix_ingest.py", "neuronix_ingest.py"),
        (Path(__file__).parent / "neuronix_query.py", "neuronix_query.py"),
    ]
    
    for file_path, name in files_to_check:
        if check_file_exists(file_path, name):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # 2. Directories
    logger.info("\n📁 Checking directories...")
    
    base_dir = Path(__file__).parent.parent
    docs_dir = base_dir / "docs"
    data_dir = base_dir / "data"
    vector_db_dir = data_dir / "vector_db"
    
    if check_directory_exists(docs_dir, "docs/ (PDF storage)", check_pdfs=True):
        checks_passed += 1
    else:
        checks_failed += 1
    
    if check_directory_exists(data_dir, "data/"):
        checks_passed += 1
    else:
        logger.info(f"  📌 Creating data/ directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
        checks_passed += 1
    
    if check_directory_exists(vector_db_dir, "data/vector_db/ (ChromaDB)"):
        checks_passed += 1
    else:
        logger.info(f"  📌 Database will be created during ingestion")
        checks_failed += 1  # Not critical yet
    
    # 3. Python Packages
    logger.info("\n📦 Checking Python packages...")
    
    packages_to_check = [
        ("sentence-transformers", None),
        ("langchain", None),
        ("langchain_community", None),
        ("langchain_chroma", None),
        ("langchain_google_genai", None),
        ("chromadb", None),
        ("google.generativeai", "google"),
        ("pypdf", None),
    ]
    
    for package, import_name in packages_to_check:
        if check_python_package(package, import_name or package):
            checks_passed += 1
        else:
            checks_failed += 1
    
    # 4. Environment Variables
    logger.info("\n🔑 Checking environment variables...")
    
    if check_env_variable("GOOGLE_API_KEY"):
        checks_passed += 1
    else:
        checks_failed += 1
    
    # 5. Configuration
    logger.info("\n⚙️  Checking configuration...")
    
    try:
        import neuronix_constants as nc
        
        logger.info(f"  ✅ Embedding Model: {nc.EMBEDDING_MODEL}")
        logger.info(f"  ✅ Collection Name: {nc.COLLECTION_NAME}")
        logger.info(f"  ✅ Batch Size: {nc.INGESTION_BATCH_SIZE}")
        logger.info(f"  ✅ Retrieval K: {nc.RETRIEVAL_K_MIN}-{nc.RETRIEVAL_K_MAX}")
        
        checks_passed += 1
        
    except Exception as e:
        logger.info(f"  ❌ Configuration error: {e}")
        checks_failed += 1
    
    # 6. Database
    logger.info("\n📊 Checking vector database...")
    
    if check_database():
        checks_passed += 1
    else:
        logger.info("    📌 Database will be populated during ingestion")
        checks_failed += 0  # Not critical yet
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("📋 VERIFICATION SUMMARY")
    logger.info("="*80)
    logger.info(f"\n✅ Passed: {checks_passed}")
    logger.info(f"⚠️  Issues: {checks_failed}")
    
    if checks_failed == 0:
        logger.info("\n🎉 System is ready!")
        logger.info("\nNext steps:")
        logger.info("  1. Ensure PDFs are in docs/ directory")
        logger.info("  2. Run: python scripts/neuronix_ingest.py")
        logger.info("  3. Run: python scripts/neuronix_query.py")
        return 0
    else:
        logger.info("\n⚠️  Some issues found. Fix them before running.")
        logger.info("\nCommon fixes:")
        logger.info("  • Install missing packages: pip install -r requirements.txt")
        logger.info("  • Set Google API key: $env:GOOGLE_API_KEY = 'your-key'")
        logger.info("  • Add PDFs to docs/ directory")
        return 1


if __name__ == "__main__":
    sys.exit(main())
