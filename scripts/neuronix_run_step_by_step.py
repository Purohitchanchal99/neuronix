"""
neuronix_run_step_by_step.py
============================
Execute the Neuronix system with detailed step-by-step guidance.

This script automates the setup process and validates each step.
Run: python scripts/neuronix_run_step_by_step.py
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.ENDC}\n")


def print_step(number, text):
    print(f"{Colors.BOLD}{Colors.BLUE}STEP {number}: {text}{Colors.ENDC}")


def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")


def main():
    print_header("🧠 NEURONIX SETUP & RUN GUIDE")
    
    print("Welcome to Neuronix - Clinical Psychology AI Assistant!")
    print("This guide will walk you through setup and execution.\n")
    
    # STEP 1: Environment Setup
    print_step(1, "Check and prepare Python environment")
    
    project_root = Path(__file__).parent.parent
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"Python version: {python_version}")
    
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ required!")
        return 1
    
    print_success("Python version is compatible")
    
    # Check virtual environment
    venv_path = project_root / "venv"
    if venv_path.exists():
        print_success("Virtual environment exists")
    else:
        print_warning("Virtual environment not found. Creating...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print_success("Virtual environment created")
        except subprocess.CalledProcessError:
            print_error("Failed to create virtual environment")
            return 1
    
    # STEP 2: Install Dependencies
    print_step(2, "Install required packages")
    
    requirements_file = project_root / "requirements.txt"
    
    print_info(f"Installing packages from {requirements_file}...")
    print("This may take 2-5 minutes on first run...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)],
            check=True,
            cwd=str(project_root)
        )
        print_success("All packages installed successfully")
    except subprocess.CalledProcessError:
        print_error("Failed to install packages")
        print_info("Try running: pip install -r requirements.txt")
        return 1
    
    # STEP 3: Check Configuration
    print_step(3, "Verify configuration")
    
    try:
        os.chdir(str(project_root / "scripts"))
        import neuronix_constants as nc
        
        print(f"Embedding Model:    {nc.EMBEDDING_MODEL}")
        print(f"Batch Size:         {nc.INGESTION_BATCH_SIZE} PDFs")
        print(f"Chunk Size:         {nc.CHUNK_SIZE} chars")
        print(f"Retrieval Range:    {nc.RETRIEVAL_K_MIN}-{nc.RETRIEVAL_K_MAX}")
        print(f"Monitoring Interval: {nc.MONITORING_INTERVAL_SECONDS} seconds")
        
        print_success("Configuration loaded successfully")
        
    except Exception as e:
        print_error(f"Configuration error: {e}")
        return 1
    
    # STEP 4: Verify Files
    print_step(4, "Check required files")
    
    required_files = [
        ("scripts", "neuronix_constants.py"),
        ("scripts", "neuronix_ingest.py"),
        ("scripts", "neuronix_query.py"),
    ]
    
    for dir_name, file_name in required_files:
        file_path = project_root / dir_name / file_name
        if file_path.exists():
            print_success(f"{file_name} found")
        else:
            print_error(f"{file_name} not found at {file_path}")
            return 1
    
    # STEP 5: Verify Directories
    print_step(5, "Check required directories")
    
    dirs_to_check = [
        ("docs", "PDFs source directory"),
        ("data", "Data storage directory"),
    ]
    
    for dir_name, description in dirs_to_check:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print_success(f"{description}: {dir_path}")
        else:
            print_warning(f"Creating {description}: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
            print_success(f"{description} created")
    
    # STEP 6: Check PDFs
    print_step(6, "Verify PDF documents available")
    
    docs_dir = project_root / "docs"
    pdfs = list(docs_dir.rglob("*.pdf"))
    
    if pdfs:
        print_success(f"Found {len(pdfs)} PDF files")
        print_info(f"Sample PDFs: {', '.join([p.name for p in pdfs[:3]])}")
    else:
        print_warning("No PDFs found in docs/ directory")
        print_info("Add PDF files to continue with ingestion")
    
    # STEP 7: Check API Key
    print_step(7, "Verify Google API configuration")
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        masked_key = api_key[:10] + "..." + api_key[-5:]
        print_success(f"GOOGLE_API_KEY set: {masked_key}")
    else:
        print_warning("GOOGLE_API_KEY not set")
        print_info("To set it, run in PowerShell:")
        print(f"{Colors.CYAN}  $env:GOOGLE_API_KEY = 'your-key-here'{Colors.ENDC}")
        print_info("Or create .env file with: GOOGLE_API_KEY=your-key")
    
    # STEP 8: Run Verification
    print_step(8, "Run system verification")
    
    print_info("Running verify_neuronix.py...")
    
    try:
        result = subprocess.run(
            [sys.executable, "verify_neuronix.py"],
            capture_output=True,
            text=True,
            cwd=str(project_root / "scripts")
        )
        
        if result.returncode == 0:
            print_success("System verification passed!")
        else:
            print_warning("Some verification issues found")
            print(result.stdout)
    except Exception as e:
        print_warning(f"Could not run verification: {e}")
    
    # STEP 9: Menu
    print_step(9, "Ready to run Neuronix")
    
    print_header("🚀 SELECT AN ACTION")
    
    print("1. Run Ingestion Pipeline (import PDFs)")
    print("2. Run Query System (interactive questions)")
    print("3. Exit\n")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        print_header("Starting Ingestion Pipeline")
        print_info("Importing HuggingFace model (first time may take 1-2 min)...")
        print_info("Processing PDFs in batches of 10...")
        print_info("Checkpoints saved after each batch")
        print_info("Progress reported every 2 minutes\n")
        
        input("Press Enter to start...")
        
        try:
            subprocess.run(
                [sys.executable, "neuronix_ingest.py"],
                cwd=str(project_root / "scripts"),
                check=False
            )
        except KeyboardInterrupt:
            print_warning("Ingestion interrupted by user")
        except Exception as e:
            print_error(f"Ingestion error: {e}")
        
        return 0
    
    elif choice == "2":
        print_header("Starting Query System")
        print_info("Loading embeddings and vector database...")
        print_info("Enter questions about clinical psychology")
        print_info("Type 'quit' to exit\n")
        
        input("Press Enter to start...")
        
        try:
            subprocess.run(
                [sys.executable, "neuronix_query.py"],
                cwd=str(project_root / "scripts"),
                check=False
            )
        except KeyboardInterrupt:
            print_warning("Query system interrupted by user")
        except Exception as e:
            print_error(f"Query error: {e}")
        
        return 0
    
    elif choice == "3":
        print_info("Goodbye!")
        return 0
    
    else:
        print_error("Invalid choice")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)
