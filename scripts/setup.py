#!/usr/bin/env python3
"""
Neuronix - Setup and Installation Script
Installs all required Python dependencies for Neuronix (downloader + RAG pipeline)
"""

import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install all required Python packages"""
    print("=" * 80)
    print("NEURONIX - Installing Dependencies")
    print("=" * 80)
    
    requirements = [
        # Downloader dependencies
        'requests',
        'beautifulsoup4',
        # Core LangChain
        'langchain==0.1.0',
        # RAG pipeline dependencies
        'langchain-community==0.0.20',
        'langchain-google-genai==0.0.8',
        'google-generativeai==0.3.0',
        'pypdf==3.17.1'
    ]
    
    print(f"\nInstalling {len(requirements)} packages...")
    print("-" * 80)
    
    for package in requirements:
        display_name = package.split("==")[0]
        print(f"\n▶ Installing {display_name}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package, "-q"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"✓ {display_name} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {display_name}: {e}")
            return False
    
    print("\n" + "=" * 80)
    print("✓ All dependencies installed successfully!")
    print("=" * 80)
    print("\nAvailable commands:")
    print("  1. Downloader:  python scripts/downloader.py")
    print("  2. RAG Pipeline: python scripts/ingest_data.py")
    print("     (requires GOOGLE_API_KEY environment variable)")
    print("  3. RAG Query:    python scripts/query_rag.py (coming soon)")
    print("\nSee RAG_PIPELINE.md for detailed instructions")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = install_requirements()
    sys.exit(0 if success else 1)

