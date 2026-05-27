#!/usr/bin/env python3
"""
Neuronix Ingestion Monitor - Real-time Progress Tracker
========================================================
Monitors ingestion_log.txt every 2 minutes and reports:
- PDFs processed
- Chunks created
- Embeddings generated
- Errors and skipped files
"""

import time
import re
import os
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent
LOG_FILE = BASE_DIR / "scripts" / "ingest_log.txt"

class IngestionMonitor:
    def __init__(self):
        self.log_file = LOG_FILE
        self.last_position = 0
        self.update_count = 0
        self.start_time = datetime.now()
        
    def read_new_logs(self):
        """Read only new log content since last check"""
        if not self.log_file.exists():
            return ""
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()
                self.last_position = f.tell()
            return new_content
        except Exception as e:
            print(f"Error reading logs: {e}")
            return ""
    
    def read_all_logs(self):
        """Read entire log file"""
        if not self.log_file.exists():
            return ""
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading logs: {e}")
            return ""
    
    def extract_metrics(self):
        """Extract key metrics from logs"""
        content = self.read_all_logs()
        
        metrics = {
            'pdfs_processed': 0,
            'chunks_created': 0,
            'embeddings_generated': 0,
            'errors': [],
            'skipped_files': [],
            'current_phase': 'Initializing',
            'is_complete': False
        }
        
        # Extract PDFs processed
        if 'Loaded' in content and 'documents' in content:
            match = re.search(r'Loaded (\d+) documents', content)
            if match:
                metrics['pdfs_processed'] = int(match.group(1))
        
        # Extract chunks created
        if 'Created' in content and 'chunks' in content:
            match = re.search(r'Created (\d+) total chunks', content)
            if match:
                metrics['chunks_created'] = int(match.group(1))
            else:
                # Try alternate pattern
                matches = re.findall(r'(\d+) chunks created', content)
                if matches:
                    metrics['chunks_created'] = sum(int(m) for m in matches)
        
        # Extract embeddings
        if 'Stored' in content and 'embeddings' in content:
            match = re.search(r'Stored (\d+) embeddings', content)
            if match:
                metrics['embeddings_generated'] = int(match.group(1))
        
        # Extract errors
        errors = re.findall(r'\[ERROR\]|\[ERROR:.*?\]|(Error|ERROR|Exception|FAILED|FAIL).*?(?=\n|$)', content)
        if errors:
            unique_errors = []
            for error in errors:
                if isinstance(error, tuple):
                    error = error[0]
                if error and error not in unique_errors:
                    unique_errors.append(str(error)[:100])  # First 100 chars
            metrics['errors'] = unique_errors[:5]  # Keep last 5 unique errors
        
        # Extract skipped files
        skipped = re.findall(r'(?:Skipped|SKIPPED):?\s*(.*?)(?=\n|$)', content)
        if skipped:
            metrics['skipped_files'] = list(set(s.strip()[:80] for s in skipped))[:5]
        
        # Determine current phase
        if 'PHASE 5' in content and 'Verification' in content:
            metrics['current_phase'] = 'PHASE 5: Verification'
        elif 'PHASE 4' in content and 'Ingesting' in content:
            metrics['current_phase'] = 'PHASE 4: Ingesting Chunks'
        elif 'PHASE 3' in content and 'Database' in content:
            metrics['current_phase'] = 'PHASE 3: Initializing Database'
        elif 'PHASE 2' in content and 'Chunks' in content:
            metrics['current_phase'] = 'PHASE 2: Creating Chunks'
        elif 'PHASE 1' in content:
            metrics['current_phase'] = 'PHASE 1: Loading Documents'
        
        # Check if complete
        if any(phrase in content for phrase in ['COMPLETE', 'successfully completed', 'Pipeline finished', 'INGESTION COMPLETE']):
            metrics['is_complete'] = True
        
        return metrics
    
    def display_status(self):
        """Display current status"""
        metrics = self.extract_metrics()
        self.update_count += 1
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] UPDATE #{self.update_count} - {metrics['current_phase']}")
        print(f"[STATUS] PDFs processed: {metrics['pdfs_processed']} / 279")
        print(f"[STATUS] Chunks created: {metrics['chunks_created']}")
        print(f"[STATUS] Embeddings generated: {metrics['embeddings_generated']}")
        
        if metrics['errors']:
            print(f"[ERRORS] {len(metrics['errors'])} error(s) detected:")
            for error in metrics['errors']:
                print(f"         {error[:100]}")
        else:
            print("[ERRORS] None")
        
        if metrics['skipped_files']:
            print(f"[SKIPPED] {len(metrics['skipped_files'])} file(s)")
        
        return metrics['is_complete']
    
    def run(self, max_updates=60):
        """Run monitoring loop"""
        print("=" * 80)
        print("NEURONIX INGESTION MONITOR".center(80, "="))
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Monitoring: {self.log_file}")
        print(f"Target: 279 PDFs")
        print("")
        
        # Initial wait for log file to exist
        wait_time = 0
        while not self.log_file.exists() and wait_time < 30:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for ingestion to start...")
            time.sleep(2)
            wait_time += 2
        
        update = 0
        while update < max_updates:
            is_complete = self.display_status()
            
            if is_complete:
                metrics = self.extract_metrics()
                print("\n" + "=" * 80)
                print(f"✅ Ingestion complete: {metrics['pdfs_processed']} PDFs processed, {metrics['chunks_created']} chunks stored, {metrics['embeddings_generated']} embeddings generated.")
                print("=" * 80)
                break
            
            update += 1
            if update < max_updates:
                print(f"[Next update in 2 minutes...]")
                time.sleep(120)  # Wait 2 minutes
        
        if update == max_updates:
            print("\n[WARNING] Monitoring timeout reached")

if __name__ == "__main__":
    monitor = IngestionMonitor()
    monitor.run()
