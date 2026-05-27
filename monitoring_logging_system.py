"""
📊 REAL-TIME MONITORING & STRUCTURED LOGGING
==============================================
Tracks: PDFs processed, chunks created, embeddings, errors
Updates every 2 minutes with detailed status
"""

import logging
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# MONITORING MODELS
# ============================================================================

class IngestionStatus(Enum):
    """Status of ingestion process"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_FAILED = "partially_failed"


@dataclass
class PDFMetrics:
    """Metrics for a single PDF"""
    pdf_name: str
    status: str
    total_pages: int = 0
    pages_processed: int = 0
    chunks_created: int = 0
    embeddings_stored: int = 0
    errors_encountered: List[str] = None
    start_time: str = None
    end_time: str = None
    duration_seconds: float = 0.0
    success_rate: float = 0.0
    
    def __post_init__(self):
        if self.errors_encountered is None:
            self.errors_encountered = []
        if self.start_time is None:
            self.start_time = datetime.now().isoformat()


@dataclass
class BatchMetrics:
    """Metrics for a batch of PDFs"""
    batch_id: str
    total_pdfs: int = 0
    pdfs_processed: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    errors: List[str] = None
    start_time: str = None
    end_time: str = None
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.start_time is None:
            self.start_time = datetime.now().isoformat()


# ============================================================================
# MONITORING ENGINE
# ============================================================================

class IngestionMonitor:
    """
    Real-time ingestion monitoring
    Updates every 2 minutes with detailed status
    """
    
    def __init__(self, logs_dir: str = "monitoring_logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.pdf_metrics: Dict[str, PDFMetrics] = {}
        self.batch_metrics: Dict[str, BatchMetrics] = {}
        self.current_batch: Optional[str] = None
        
        self.start_time = datetime.now()
        self.last_update = datetime.now()
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        
        logger.info(f"✅ IngestionMonitor initialized: {logs_dir}")
    
    def start_batch(self, batch_id: str) -> BatchMetrics:
        """Start monitoring a new batch"""
        batch_metrics = BatchMetrics(batch_id=batch_id)
        self.batch_metrics[batch_id] = batch_metrics
        self.current_batch = batch_id
        
        logger.info(f"🚀 Batch started: {batch_id}")
        return batch_metrics
    
    def register_pdf(self, batch_id: str, pdf_name: str, total_pages: int) -> PDFMetrics:
        """Register a PDF for tracking"""
        pdf_metrics = PDFMetrics(
            pdf_name=pdf_name,
            status=IngestionStatus.PENDING.value,
            total_pages=total_pages
        )
        
        key = f"{batch_id}:{pdf_name}"
        self.pdf_metrics[key] = pdf_metrics
        
        # Update batch
        if batch_id in self.batch_metrics:
            self.batch_metrics[batch_id].total_pdfs += 1
        
        logger.info(f"📄 PDF registered: {pdf_name} ({total_pages} pages)")
        return pdf_metrics
    
    def update_pdf_progress(self, batch_id: str, pdf_name: str, 
                           pages_processed: int, chunks_created: int,
                           embeddings_stored: int):
        """Update progress for a PDF"""
        key = f"{batch_id}:{pdf_name}"
        
        if key in self.pdf_metrics:
            metrics = self.pdf_metrics[key]
            metrics.pages_processed = pages_processed
            metrics.chunks_created = chunks_created
            metrics.embeddings_stored = embeddings_stored
            metrics.status = IngestionStatus.IN_PROGRESS.value
    
    def log_pdf_error(self, batch_id: str, pdf_name: str, error: str):
        """Log error for a PDF"""
        key = f"{batch_id}:{pdf_name}"
        
        if key in self.pdf_metrics:
            self.pdf_metrics[key].errors_encountered.append(error)
            logger.error(f"❌ Error in {pdf_name}: {error}")
    
    def complete_pdf(self, batch_id: str, pdf_name: str):
        """Mark PDF as completed"""
        key = f"{batch_id}:{pdf_name}"
        
        if key in self.pdf_metrics:
            metrics = self.pdf_metrics[key]
            metrics.end_time = datetime.now().isoformat()
            metrics.status = IngestionStatus.COMPLETED.value if not metrics.errors_encountered else IngestionStatus.PARTIALLY_FAILED.value
            
            # Calculate metrics
            if metrics.total_pages > 0:
                metrics.success_rate = (metrics.pages_processed / metrics.total_pages) * 100
            
            logger.info(f"✅ PDF completed: {pdf_name} (Success Rate: {metrics.success_rate:.1f}%)")
    
    def complete_batch(self, batch_id: str):
        """Mark batch as completed"""
        if batch_id in self.batch_metrics:
            batch = self.batch_metrics[batch_id]
            batch.end_time = datetime.now().isoformat()
            
            # Calculate totals
            batch_pdfs = [m for k, m in self.pdf_metrics.items() if k.startswith(f"{batch_id}:")]
            batch.pdfs_processed = len([p for p in batch_pdfs if p.status != IngestionStatus.PENDING.value])
            batch.total_chunks = sum(p.chunks_created for p in batch_pdfs)
            batch.total_embeddings = sum(p.embeddings_stored for p in batch_pdfs)
            
            logger.info(f"🎉 Batch completed: {batch_id}")
    
    def start_periodic_monitoring(self, interval_minutes: int = 2):
        """Start periodic monitoring thread"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_minutes,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"📊 Periodic monitoring started (every {interval_minutes} minutes)")
    
    def _monitoring_loop(self, interval_minutes: int):
        """Monitoring loop that runs at specified intervals"""
        while self.monitoring_active:
            time.sleep(interval_minutes * 60)
            self._publish_status_update()
    
    def _publish_status_update(self):
        """Publish status update"""
        status = self.get_current_status()
        self._log_status_update(status)
        logger.info(f"📊 Status Update: {status['summary']}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("⛔ Monitoring stopped")
    
    def get_current_status(self) -> Dict:
        """Get current status snapshot"""
        total_pdfs = sum(1 for m in self.pdf_metrics.values())
        completed_pdfs = sum(1 for m in self.pdf_metrics.values() if m.status == IngestionStatus.COMPLETED.value)
        failed_pdfs = sum(1 for m in self.pdf_metrics.values() if m.status == IngestionStatus.FAILED.value)
        
        total_chunks = sum(m.chunks_created for m in self.pdf_metrics.values())
        total_embeddings = sum(m.embeddings_stored for m in self.pdf_metrics.values())
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "pdfs_total": total_pdfs,
                "pdfs_completed": completed_pdfs,
                "pdfs_failed": failed_pdfs,
                "chunks_created": total_chunks,
                "embeddings_stored": total_embeddings,
                "elapsed_seconds": elapsed
            },
            "pdf_metrics": [asdict(m) for m in self.pdf_metrics.values()],
            "batch_metrics": [asdict(m) for m in self.batch_metrics.values()]
        }
    
    def save_status_report(self):
        """Save status report to disk"""
        status = self.get_current_status()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report_file = self.logs_dir / f"status_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Status report saved: {report_file}")
        return report_file


# ============================================================================
# STRUCTURED LOGGING
# ============================================================================

class StructuredLogger:
    """Structured logging in JSON/CSV formats"""
    
    def __init__(self, logs_dir: str = "structured_logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self.events = []
        logger.info(f"✅ StructuredLogger initialized: {logs_dir}")
    
    def log_event(self, event_type: str, **kwargs):
        """
        Log a structured event
        
        Example:
        logger.log_event(
            "pdf_ingested",
            pdf_name="dsm5.pdf",
            chunks_created=100,
            duration_seconds=45.2
        )
        """
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            **kwargs
        }
        
        self.events.append(event)
    
    def save_logs(self, format: str = "json"):
        """
        Save logs to disk
        format: json or csv
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            log_file = self.logs_dir / f"logs_{timestamp}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            import csv
            log_file = self.logs_dir / f"logs_{timestamp}.csv"
            
            if self.events:
                with open(log_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.events[0].keys())
                    writer.writeheader()
                    writer.writerows(self.events)
        
        logger.info(f"✅ Logs saved: {log_file}")
        return log_file
    
    def get_error_summary(self) -> List[Dict]:
        """Get summary of all errors"""
        errors = [e for e in self.events if e.get("event_type") == "error"]
        return errors
    
    def get_statistics(self) -> Dict:
        """Get statistics of logged events"""
        event_counts = {}
        for event in self.events:
            event_type = event.get("event_type")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "total_events": len(self.events),
            "event_types": event_counts,
            "errors": len([e for e in self.events if e.get("event_type") == "error"])
        }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example: Monitoring
    monitor = IngestionMonitor()
    monitor.start_periodic_monitoring(interval_minutes=2)
    
    # Start batch
    batch_id = "batch_001"
    monitor.start_batch(batch_id)
    
    # Register PDFs
    monitor.register_pdf(batch_id, "dsm5.pdf", 500)
    monitor.register_pdf(batch_id, "icd11.pdf", 400)
    
    # Simulate progress
    monitor.update_pdf_progress(batch_id, "dsm5.pdf", 100, 250, 250)
    time.sleep(1)
    monitor.update_pdf_progress(batch_id, "dsm5.pdf", 500, 1000, 1000)
    monitor.complete_pdf(batch_id, "dsm5.pdf")
    
    # Structured logging
    logger_struct = StructuredLogger()
    logger_struct.log_event("pdf_ingested", pdf_name="dsm5.pdf", chunks=1000)
    logger_struct.log_event("embedding_stored", count=1000)
    
    print(f"\n📊 Status: {monitor.get_current_status()['summary']}")
    print(f"📊 Stats: {logger_struct.get_statistics()}")
