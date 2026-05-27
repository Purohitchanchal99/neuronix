"""
Real-time Ingestion Pipeline Monitor
====================================
Tracks progre ss of RAG vector database population every 2 minutes.

Shows:
- PDFs processed
- Chunks created
- Embeddings generated
- Errors/skipped files
"""

import os
import time
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
LOG_FILE = BASE_DIR / "scripts" / "ingest_log.txt"
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"

class IngestionMonitor:
    """Monitor RAG ingestion pipeline progress"""
    
    def __init__(self):
        self.log_file = LOG_FILE
        self.last_position = 0
        self.stats = {
            'pdfs_processed': 0,
            'chunks_created': 0,
            'embeddings_stored': 0,
            'errors': [],
            'skipped_files': [],
            'phases_completed': [],
            'current_phase': None,
            'start_time': None,
            'last_update': datetime.now()
        }
    
    def read_new_logs(self):
        """Read only new log entries since last check"""
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
    
    def parse_logs(self, content):
        """Extract progress information from log content"""
        if not content.strip():
            return
        
        lines = content.split('\n')
        
        for line in lines:
            # Track current phase
            if 'PHASE' in line and 'Loading Documents' in line and 'PHASE 1' in line:
                self.stats['current_phase'] = 'PHASE 1: Loading Documents'
            elif 'PHASE 2' in line and 'Creating Chunks' in line:
                self.stats['current_phase'] = 'PHASE 2: Creating Chunks'
                if 'PHASE 1' not in self.stats['phases_completed']:
                    self.stats['phases_completed'].append('PHASE 1: Loading')
            elif 'PHASE 3' in line and 'Initializing' in line:
                self.stats['current_phase'] = 'PHASE 3: Initializing Database'
            elif 'PHASE 4' in line and 'Ingesting' in line:
                self.stats['current_phase'] = 'PHASE 4: Ingesting Chunks'
            elif 'PHASE 5' in line and 'Verification' in line:
                self.stats['current_phase'] = 'PHASE 5: Verification'
            
            # Track started time
            if 'NEURONIX RAG DATA INGESTION PIPELINE' in line and 'Started:' in line:
                # Extract timestamp from next few lines
                self.stats['start_time'] = datetime.now()
            
            # Count documents loaded
            if '[OK] Loaded' in line and 'documents' in line:
                match = re.search(r'Loaded (\d+) documents', line)
                if match:
                    self.stats['pdfs_processed'] = int(match.group(1))
            
            # Count chunks created
            if '[OK] Created' in line and 'chunks' in line:
                match = re.search(r'Created (\d+) total chunks', line)
                if match:
                    self.stats['chunks_created'] = int(match.group(1))
            
            # Track individual file chunks
            if '[OK]' in line and 'chunks created' in line:
                match = re.search(r'(\d+) chunks created', line)
                if match:
                    # This is a file-level chunk count
                    pass
            
            # Track embeddings stored
            if 'Stored batch' in line:
                match = re.search(r'Stored batch (\d+): (\d+) chunks', line)
                if match:
                    batch_num = int(match.group(1))
                    chunk_count = int(match.group(2))
                    self.stats['embeddings_stored'] += chunk_count
            
            if 'Total chunks stored:' in line:
                match = re.search(r'Total chunks stored: (\d+)', line)
                if match:
                    self.stats['embeddings_stored'] = int(match.group(1))
            
            # Track errors
            if 'ERROR' in line or 'Error' in line:
                error_msg = line.split(' - ')[-1] if ' - ' in line else line
                if error_msg not in self.stats['errors']:
                    self.stats['errors'].append(error_msg[:100])  # Keep first 100 chars
            
            # Track completed phases
            if 'verification successful' in line.lower():
                self.stats['phases_completed'].append('PHASE 5: Verification')
        
        self.stats['last_update'] = datetime.now()
    
    def get_vector_db_size(self):
        """Get current vector database size on disk"""
        if not VECTOR_DB_DIR.exists():
            return 0
        
        total_size = 0
        for filepath in VECTOR_DB_DIR.rglob('*'):
            if filepath.is_file():
                total_size += filepath.stat().st_size
        
        return total_size / (1024 * 1024)  # Convert to MB
    
    def print_progress(self):
        """Print formatted progress report"""
        elapsed = ""
        if self.stats['start_time']:
            elapsed_sec = (datetime.now() - self.stats['start_time']).total_seconds()
            mins = int(elapsed_sec // 60)
            secs = int(elapsed_sec % 60)
            elapsed = f" [{mins}m {secs}s elapsed]"
        
        db_size = self.get_vector_db_size()
        
        print("\n" + "="*70)
        print(f"📊 INGESTION PIPELINE MONITOR{elapsed}")
        print("="*70)
        
        print(f"\n📁 PROCESSING STATUS:")
        print(f"   PDFs Loaded:           {self.stats['pdfs_processed']}/279")
        print(f"   Chunks Created:        {self.stats['chunks_created']:,}")
        print(f"   Embeddings Stored:     {self.stats['embeddings_stored']:,}")
        print(f"   Vector DB Size:        {db_size:.2f} MB")
        
        print(f"\n🔄 PIPELINE PHASES:")
        for phase in ['PHASE 1: Loading', 'PHASE 2: Creating Chunks', 'PHASE 3: Initializing Database', 'PHASE 4: Ingesting Chunks', 'PHASE 5: Verification']:
            status = "✅" if phase in self.stats['phases_completed'] else "⏳" if self.stats['current_phase'] and phase.split(':')[0] in self.stats['current_phase'] else "⭐"
            print(f"   {status} {phase}")
        
        if self.stats['current_phase']:
            print(f"\n   🎯 Currently: {self.stats['current_phase']}")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ({len(self.stats['errors'])}):")
            for error in self.stats['errors'][-5:]:  # Show last 5 errors
                print(f"   ❌ {error}")
        
        print("\n" + "="*70)
    
    def monitor_continuous(self, interval_seconds=120):
        """Continuously monitor ingestion every N seconds"""
        print(f"🚀 Starting ingestion monitor (updating every {interval_seconds}s)\n")
        
        monitor_count = 0
        while True:
            monitor_count += 1
            
            # Read new logs
            new_logs = self.read_new_logs()
            self.parse_logs(new_logs)
            
            # Print current progress
            self.print_progress()
            
            # Check if pipeline is complete
            if 'PHASE 5: Verification' in self.stats['phases_completed'] or (
                self.stats['embeddings_stored'] > 0 and 
                'Pipeline completed successfully' in new_logs
            ):
                print("\n✅ INGESTION COMPLETE!")
                self.print_final_summary()
                break
            
            # Check for critical errors
            if any('Fatal error' in err for err in self.stats['errors']):
                print("\n❌ FATAL ERROR DETECTED - Pipeline failed")
                break
            
            # Wait before next check
            try:
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\n\n⏹️  Monitor stopped by user")
                break
    
    def print_final_summary(self):
        """Print final ingestion summary"""
        print("\n" + "="*70)
        print("✅ INGESTION PIPELINE SUMMARY")
        print("="*70)
        
        elapsed = ""
        if self.stats['start_time']:
            elapsed_sec = (datetime.now() - self.stats['start_time']).total_seconds()
            mins = int(elapsed_sec // 60)
            secs = int(elapsed_sec % 60)
            elapsed = f"{mins}m {secs}s"
        
        db_size = self.get_vector_db_size()
        
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   Total PDFs Processed:  {self.stats['pdfs_processed']}")
        print(f"   Total Chunks Created:  {self.stats['chunks_created']:,}")
        print(f"   Total Embeddings:      {self.stats['embeddings_stored']:,}")
        print(f"   Vector DB Size:        {db_size:.2f} MB")
        print(f"   Total Time:            {elapsed}")
        
        if self.stats['embeddings_stored'] > 0 and self.stats['chunks_created'] > 0:
            avg_chunk_size = self.stats['embeddings_stored'] / max(1, self.stats['chunks_created'])
            print(f"   Avg Embeddings/Chunk:  {avg_chunk_size:.2f}")
        
        print(f"\n✅ COMPLETED PHASES: {len(self.stats['phases_completed'])}/5")
        for phase in self.stats['phases_completed']:
            print(f"   ✓ {phase}")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ENCOUNTERED: {len(self.stats['errors'])}")
            print("   (These may be non-fatal warnings)")
        
        print("\n" + "="*70)
        print("🎉 Vector database is ready for RAG queries!")
        print("="*70 + "\n")


if __name__ == "__main__":
    monitor = IngestionMonitor()
    
    # Check if ingestion is already running
    if not LOG_FILE.exists():
        print(f"⚠️  Log file not found: {LOG_FILE}")
        print("Make sure ingestion script is running: python scripts/ingest_data.py\n")
    else:
        print("✅ Log file found, starting monitor...\n")
    
    # Monitor every 2 minutes (120 seconds)
    monitor.monitor_continuous(interval_seconds=120)
