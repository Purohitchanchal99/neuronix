#!/usr/bin/env python3
"""
Neuronix Ingestion Monitor - Enhanced Real-time Progress Tracker
================================================================
Monitors ingestion process every 2 minutes and reports:
- PDFs processed / remaining
- Chunks created
- Embeddings generated
- Errors and skipped files
- Estimated time to completion

Usage:
    python ingestion_monitor_enhanced.py
"""

import time
import re
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sqlite3

# ================================================================
# PATHS
# ================================================================
BASE_DIR = Path(__file__).parent
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"
DOCS_DIR = BASE_DIR / "docs"
LOGS_DIR = BASE_DIR / "scripts"
INGEST_LOG = LOGS_DIR / "neuronix_ingest.log"
MONITORING_LOG = LOGS_DIR / "neuronix_monitoring.log"
CHECKPOINT_FILE = BASE_DIR / "data" / "progress.txt"

# Configuration
MONITORING_INTERVAL = 120  # 2 minutes in seconds
CHROMADB_COLLECTION = "neuronix_medical_kb"


class IngestionMonitor:
    """Monitor and report ingestion progress every 2 minutes"""
    
    def __init__(self):
        """Initialize monitor"""
        self.start_time = datetime.now()
        self.last_position = 0
        self.update_count = 0
        
        # Initialize metrics
        self.metrics = {
            'pdfs_processed': 0,
            'pdfs_failed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'errors': [],
            'skipped_files': [],
            'current_phase': 'Initializing',
            'is_complete': False,
            'chroma_doc_count': 0
        }
        
        # Get total PDFs to process
        self.total_pdfs = self._count_pdf_files()
        
    def _count_pdf_files(self) -> int:
        """Count total PDF files in docs directory"""
        if not DOCS_DIR.exists():
            return 0
        
        pdf_count = 0
        for root, dirs, files in os.walk(DOCS_DIR):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_count += 1
        return pdf_count
    
    def _count_chroma_documents(self) -> int:
        """Count documents in ChromaDB collection"""
        try:
            db_path = VECTOR_DB_DIR / "chroma.sqlite3"
            if not db_path.exists():
                return 0
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Query the documents table
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            return 0
    
    def read_checkpoint(self) -> Dict:
        """Read checkpoint data"""
        if not CHECKPOINT_FILE.exists():
            return {}
        
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                return data
        except:
            return {}
    
    def read_new_logs(self) -> str:
        """Read only new log entries since last check"""
        if not INGEST_LOG.exists():
            return ""
        
        try:
            with open(INGEST_LOG, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()
            return new_content
        except Exception as e:
            print(f"Error reading logs: {e}")
            return ""
    
    def read_all_logs(self) -> str:
        """Read entire log file"""
        if not INGEST_LOG.exists():
            return ""
        
        try:
            with open(INGEST_LOG, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading logs: {e}")
            return ""
    
    def extract_metrics_from_logs(self):
        """Extract metrics from ingestion logs"""
        content = self.read_all_logs()
        
        # Extract PDFs processed
        pdfs = re.findall(r'Processing PDF \((\d+)/(\d+)\):', content)
        if pdfs:
            self.metrics['pdfs_processed'] = int(pdfs[-1][0])
            self.total_pdfs = int(pdfs[-1][1])
        
        # Extract chunks created - look for total chunks in log
        chunks = re.findall(r'Created (\d+) chunks from', content)
        if chunks:
            self.metrics['chunks_created'] = sum(int(c) for c in chunks)
        
        # Also try to find total chunks line
        total_chunks = re.search(r'Created a total of (\d+) chunks', content)
        if total_chunks:
            self.metrics['chunks_created'] = int(total_chunks.group(1))
        
        # Extract embeddings generated
        embeddings = re.findall(r'Storing (\d+) embeddings', content)
        if embeddings:
            self.metrics['embeddings_generated'] = sum(int(e) for e in embeddings)
        
        # Extract errors
        errors = re.findall(r'❌ .*?(?=\n|$)', content)
        self.metrics['errors'] = list(set(errors))[-10:]  # Keep last 10 unique errors
        
        # Extract skipped files
        skipped = re.findall(r'⚠️  Skipping: (.*?)(?=\n|$)', content)
        self.metrics['skipped_files'] = list(set(skipped))[-10:]  # Keep last 10 unique
        
        # Check if complete
        if 'Ingestion complete' in content or 'All done' in content:
            self.metrics['is_complete'] = True
            self.metrics['current_phase'] = 'Complete ✅'
        elif 'Creating ChromaDB collection' in content:
            self.metrics['current_phase'] = 'Creating Collection'
        elif 'Storing embeddings' in content:
            self.metrics['current_phase'] = 'Storing Embeddings'
        elif 'Processing PDF' in content:
            self.metrics['current_phase'] = 'Processing PDFs'
        
        # Get ChromaDB document count
        self.metrics['chroma_doc_count'] = self._count_chroma_documents()
        
        # Also check checkpoint file
        checkpoint = self.read_checkpoint()
        if checkpoint:
            self.metrics['pdfs_processed'] = checkpoint.get('pdf_number', self.metrics['pdfs_processed'])
            if 'chunks_created' in checkpoint:
                self.metrics['chunks_created'] = checkpoint.get('chunks_created', self.metrics['chunks_created'])
    
    def get_progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_pdfs == 0:
            return 0
        return (self.metrics['pdfs_processed'] / self.total_pdfs) * 100
    
    def get_elapsed_time(self) -> str:
        """Get elapsed time since monitor started"""
        elapsed = datetime.now() - self.start_time
        minutes, seconds = divmod(elapsed.total_seconds(), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    
    def estimate_time_remaining(self) -> str:
        """Estimate time remaining for ingestion"""
        if self.metrics['pdfs_processed'] == 0:
            return "Calculating..."
        
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        avg_time_per_pdf = elapsed_seconds / self.metrics['pdfs_processed']
        pdfs_remaining = self.total_pdfs - self.metrics['pdfs_processed']
        remaining_seconds = avg_time_per_pdf * pdfs_remaining
        
        if remaining_seconds < 0:
            return "N/A"
        
        seconds = int(remaining_seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"~{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"~{int(minutes)}m {int(seconds)}s"
        else:
            return f"~{int(seconds)}s"
    
    def print_status_report(self):
        """Print formatted status report"""
        progress_pct = self.get_progress_percentage()
        progress_bar = self._create_progress_bar(progress_pct)
        
        report = f"""
{'='*80}
🧠 NEURONIX INGESTION PROGRESS REPORT
{'='*80}
⏱️  Elapsed Time: {self.get_elapsed_time()} | Remaining: {self.estimate_time_remaining()}
📍 Current Phase: {self.metrics['current_phase']}

📊 PROGRESS METRICS:
   PDFs Processed: {self.metrics['pdfs_processed']}/{self.total_pdfs}
   Progress: {progress_bar} {progress_pct:.1f}%
   
📦 DATA CREATED:
   Total Chunks: {self.metrics['chunks_created']:,}
   ChromaDB Docs: {self.metrics['chroma_doc_count']:,}
   Embeddings: {self.metrics['embeddings_generated']:,}

❌ ERRORS & ISSUES:
   Failed PDFs: {self.metrics['pdfs_failed']}
   Unique Errors: {len(self.metrics['errors'])}
   Skipped Files: {len(self.metrics['skipped_files'])}
"""
        
        if self.metrics['errors']:
            report += f"\n   Recent Errors:\n"
            for error in self.metrics['errors'][-3:]:
                report += f"      • {error[:70]}\n"
        
        if self.metrics['skipped_files']:
            report += f"\n   Skipped Files:\n"
            for skipped in self.metrics['skipped_files'][-3:]:
                report += f"      • {skipped[:70]}\n"
        
        if self.metrics['is_complete']:
            report += f"\n✅ INGESTION COMPLETE!\n"
            report += f"   Total Time: {self.get_elapsed_time()}\n"
            report += f"   Total Chunks Created: {self.metrics['chunks_created']:,}\n"
            report += f"   Total Documents in DB: {self.metrics['chroma_doc_count']:,}\n"
        
        report += f"{'='*80}\n"
        
        print(report)
        self.update_count += 1
    
    def _create_progress_bar(self, pct: float, width: int = 30) -> str:
        """Create a simple progress bar"""
        filled = int(width * pct / 100)
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return f"[{bar}]"
    
    def log_report(self):
        """Log report to monitoring log file"""
        try:
            with open(MONITORING_LOG, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Report #{self.update_count} at {datetime.now().isoformat()} ---\n")
                f.write(f"PDFs Processed: {self.metrics['pdfs_processed']}/{self.total_pdfs}\n")
                f.write(f"Chunks Created: {self.metrics['chunks_created']:,}\n")
                f.write(f"Embeddings: {self.metrics['embeddings_generated']:,}\n")
                f.write(f"ChromaDB Docs: {self.metrics['chroma_doc_count']:,}\n")
                f.write(f"Phase: {self.metrics['current_phase']}\n")
                if self.metrics['errors']:
                    f.write(f"Recent Errors: {len(self.metrics['errors'])}\n")
                if self.metrics['skipped_files']:
                    f.write(f"Skipped Files: {len(self.metrics['skipped_files'])}\n")
                f.write("---\n")
        except Exception as e:
            print(f"Error logging report: {e}")
    
    def run(self, max_updates: int = 0):
        """Run monitoring loop every 2 minutes"""
        print("\n🚀 Starting Neuronix Ingestion Monitor...")
        print(f"📁 Watching: {INGEST_LOG}")
        print(f"📊 Total PDFs to process: {self.total_pdfs}")
        print(f"⏱️  Reporting every {MONITORING_INTERVAL} seconds\n")
        
        update_count = 0
        
        try:
            while True:
                # Extract metrics from logs
                self.extract_metrics_from_logs()
                
                # Print status
                self.print_status_report()
                
                # Log to file
                self.log_report()
                
                update_count += 1
                
                # Check if max updates reached (0 = unlimited)
                if max_updates > 0 and update_count >= max_updates:
                    print("✅ Monitor stopped (max updates reached)")
                    break
                
                # Check if ingestion is complete
                if self.metrics['is_complete']:
                    print("✅ Ingestion complete! Monitor can be stopped.")
                    print(f"   Final Summary:")
                    print(f"   - Total PDFs processed: {self.metrics['pdfs_processed']}")
                    print(f"   - Total Chunks created: {self.metrics['chunks_created']:,}")
                    print(f"   - Total Documents in DB: {self.metrics['chroma_doc_count']:,}")
                    break
                
                # Wait for next interval
                time.sleep(MONITORING_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitor stopped by user")
            self.print_status_report()
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            raise


def main():
    """Main entry point"""
    import sys
    
    # Parse arguments
    max_updates = 0
    if len(sys.argv) > 1:
        try:
            max_updates = int(sys.argv[1])
        except ValueError:
            pass
    
    # Create and run monitor
    monitor = IngestionMonitor()
    monitor.run(max_updates=max_updates)


if __name__ == "__main__":
    main()
