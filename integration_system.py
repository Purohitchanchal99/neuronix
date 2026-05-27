"""
🚀 NEURONIX POST-INGESTION INTEGRATION
======================================
Master orchestration script that combines:
1. Metadata schema + attachment
2. Semantic cleanup (Hinglish, fuzzy matching)
3. Checkpoint validation
4. Query precision layer
5. Monitoring & logging
6. Hybrid routing (Gemini + HuggingFace)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from post_ingestion_layer import (
    MetadataManager, SemanticCleanupManager, CheckpointValidator,
    ChunkMetadata, DomainTag
)
from query_precision_layer import QueryPrecisionLayer, QueryContext, DualFilterQueryRouter
from monitoring_logging_system import IngestionMonitor, StructuredLogger
from hybrid_routing_system import HybridRouter, QuotaManager, FailoverStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# INTEGRATED NEURONIX SYSTEM
# ============================================================================

class NeuronixPostIngestionSystem:
    """
    Master orchestration for post-ingestion pipeline
    
    Workflow:
    1. Ingest PDFs + attach metadata
    2. Clean semantic content (Hinglish, misspellings)
    3. Validate batches (checkpoints)
    4. Build query precision layer
    5. Enable real-time monitoring
    6. Configure hybrid routing
    """
    
    def __init__(self, config_dir: str = "neuronix_config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.metadata_manager = MetadataManager()
        self.cleanup_manager = SemanticCleanupManager()
        self.validator = CheckpointValidator()
        self.monitor = IngestionMonitor()
        self.logger_structured = StructuredLogger()
        self.router = HybridRouter()
        self.quota_manager = QuotaManager()
        
        self.ingestion_state = {
            "active": False,
            "batch_id": None,
            "current_pdf": None,
            "chunks_created": 0,
            "embeddings_stored": 0
        }
        
        logger.info("✅ NeuronixPostIngestionSystem initialized")
    
    # ========================================================================
    # PHASE 1: INGESTION WITH METADATA
    # ========================================================================
    
    def ingest_pdf_with_metadata(self, 
                                pdf_path: str,
                                batch_id: str,
                                domain_tags: List[str],
                                chapter: int,
                                section: str) -> Dict:
        """
        Ingest PDF with automatic metadata attachment
        
        Returns:
        {
            "batch_id": str,
            "pdf_file": str,
            "chunks_created": int,
            "metadata_attached": int,
            "status": str
        }
        """
        
        logger.info(f"📄 Starting ingestion: {pdf_path}")
        
        # Register PDF in monitor
        self.monitor.register_pdf(batch_id, Path(pdf_path).name, pages=1)  # Placeholder
        
        self.ingestion_state["active"] = True
        self.ingestion_state["batch_id"] = batch_id
        self.ingestion_state["current_pdf"] = pdf_path
        
        try:
            # Simulate PDF reading and chunking
            chunks = self._extract_chunks_from_pdf(pdf_path)
            
            chunks_with_metadata = []
            
            for i, chunk in enumerate(chunks):
                # Create metadata for each chunk
                metadata = self.metadata_manager.attach_metadata(
                    chunk,
                    source_pdf=Path(pdf_path).name,
                    source_url=f"pdf://{pdf_path}",
                    chapter=chapter,
                    section=section,
                    domain_tags=domain_tags,
                    difficulty_level="intermediate",
                    original_index=i
                )
                
                # Save metadata
                self.metadata_manager.save_metadata(metadata.chunk_id, metadata)
                
                chunks_with_metadata.append((chunk, metadata))
                self.ingestion_state["chunks_created"] += 1
            
            # Log ingestion event
            self.logger_structured.log_event(
                "pdf_ingested",
                pdf_name=Path(pdf_path).name,
                chunks_created=len(chunks),
                domain_tags=domain_tags,
                chapter=chapter,
                section=section
            )
            
            logger.info(f"✅ Ingested {len(chunks)} chunks with metadata")
            
            return {
                "batch_id": batch_id,
                "pdf_file": Path(pdf_path).name,
                "chunks_created": len(chunks),
                "metadata_attached": len(chunks),
                "status": "success"
            }
        
        except Exception as e:
            logger.error(f"❌ Ingestion error: {e}")
            self.logger_structured.log_event(
                "error",
                event="pdf_ingestion",
                pdf_path=pdf_path,
                error=str(e)
            )
            
            return {
                "batch_id": batch_id,
                "pdf_file": Path(pdf_path).name,
                "status": "failed",
                "error": str(e)
            }
    
    # ========================================================================
    # PHASE 2: SEMANTIC CLEANUP
    # ========================================================================
    
    def clean_and_normalize_chunks(self, 
                                  chunks: List[str],
                                  batch_id: str) -> List[Dict]:
        """
        Clean chunks: normalize, fuzzy matching, intent mapping
        
        Returns:
        [
            {
                "original": str,
                "cleaned": str,
                "intent_mapped": str,
                "cleaning_score": float
            }
        ]
        """
        
        logger.info(f"🧹 Starting semantic cleanup for {len(chunks)} chunks")
        
        cleaned_chunks = []
        
        for chunk in chunks:
            # Full cleaning pipeline
            cleaned = self.cleanup_manager.clean_query(chunk)
            
            # Calculate cleaning score
            cleaning_score = self._calculate_cleaning_score(cleaned)
            
            result = {
                "original": cleaned["original"][:100],
                "cleaned": cleaned["cleaned"],
                "intent_mapped": cleaned["intent_mapped"],
                "cleaning_score": cleaning_score
            }
            
            cleaned_chunks.append(result)
            
            # Log
            self.logger_structured.log_event(
                "chunk_cleaned",
                batch_id=batch_id,
                cleaning_score=cleaning_score
            )
        
        logger.info(f"✅ Cleaned {len(cleaned_chunks)} chunks")
        
        return cleaned_chunks
    
    @staticmethod
    def _calculate_cleaning_score(cleaned_dict: Dict) -> float:
        """Calculate quality score of cleaning (0-1)"""
        # Score based on changes made
        score = 1.0
        
        if cleaned_dict["original"] != cleaned_dict["cleaned"]:
            score = 0.9  # Minor changes
        
        if cleaned_dict["intent_mapped"] != cleaned_dict["cleaned"]:
            score = 0.8  # Significant changes
        
        return score
    
    # ========================================================================
    # PHASE 3: CHECKPOINT VALIDATION
    # ========================================================================
    
    def validate_batch_checkpoint(self, 
                                 batch_info: Dict) -> Dict:
        """
        Validate batch at checkpoint
        
        Checks:
        - Chunk count (expected vs actual)
        - Embeddings count
        - Error logs
        """
        
        logger.info("✅ Running checkpoint validation")
        
        validation_result = self.validator.validate_batch(batch_info)
        
        # Save validation log
        self.validator.save_validation_log(format="json")
        
        # Log event
        self.logger_structured.log_event(
            "batch_validated",
            batch_id=batch_info.get("batch_id"),
            status=validation_result["status"]
        )
        
        return validation_result
    
    # ========================================================================
    # PHASE 4: QUERY EXECUTION WITH PRECISION
    # ========================================================================
    
    def execute_precision_query(self,
                               query: str,
                               domain_filters: Optional[List[str]] = None,
                               user_difficulty: str = "intermediate") -> Dict:
        """
        Execute query with precision layer:
        1. Clean query (semantic cleanup)
        2. Apply metadata filters
        3. Calculate embedding similarity
        4. Rank by combined score
        5. Route through hybrid system
        
        Returns:
        {
            "query": str,
            "results": List[Dict],
            "response": str,
            "model_used": str,
            "routing_decision": Dict,
            "metadata": Dict
        }
        """
        
        logger.info(f"🎯 Executing precision query: {query}")
        
        # Step 1: Clean query
        cleaned_query = self.cleanup_manager.clean_query(query)
        logger.info(f"✅ Query cleaned: {cleaned_query['cleaned']}")
        
        # Step 2: Create query context
        context = QueryContext(
            query_text=cleaned_query["cleaned"],
            domain_filters=domain_filters,
            max_results=5
        )
        
        # Step 3: Retrieve candidates (would use ChromaDB in production)
        candidates = self._retrieve_candidates(cleaned_query["cleaned"])
        
        # Step 4: Apply precision filters
        # (In production would use QueryPrecisionLayer.execute_precision_query)
        filtered_results = self._apply_precision_filters(candidates, context)
        
        logger.info(f"✅ Retrieved {len(filtered_results)} results with precision filtering")
        
        # Step 5: Route through hybrid system
        context_str = "\n".join([r["text"][:100] for r in filtered_results])
        system_prompt = f"You are a clinical mental health expert. Difficulty level: {user_difficulty}"
        
        routed_result = self.router.route_query(
            query=cleaned_query["cleaned"],
            context=context_str,
            system_prompt=system_prompt
        )
        
        # Combine results
        final_result = {
            "original_query": query,
            "cleaned_query": cleaned_query["cleaned"],
            "results": filtered_results,
            "response": routed_result["response"],
            "model_used": routed_result["model_used"],
            "routing_decision": routed_result["routing_decision"],
            "metadata": {
                **routed_result["metadata"],
                "results_count": len(filtered_results),
                "precision_filters_applied": True
            }
        }
        
        # Log query execution
        self.logger_structured.log_event(
            "query_executed",
            query=query[:50],
            model_used=routed_result["model_used"],
            results_found=len(filtered_results)
        )
        
        return final_result
    
    # ========================================================================
    # PHASE 5: HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def _extract_chunks_from_pdf(pdf_path: str) -> List[str]:
        """Extract text chunks from PDF (placeholder)"""
        # In production: use PyPDF2, pdfplumber, etc.
        return [
            "Depression is a mental health condition...",
            "Symptoms include persistent sadness...",
            "Treatment options include therapy..."
        ]
    
    @staticmethod
    def _retrieve_candidates(query: str) -> List[Tuple[str, Dict]]:
        """Retrieve candidates from ChromaDB (placeholder)"""
        # In production: search ChromaDB with query embedding
        return [
            ("Depression description...", {"domain_tags": ["psychiatric"], "chapter": 1}),
            ("Therapy methods...", {"domain_tags": ["therapeutic"], "chapter": 3}),
        ]
    
    @staticmethod
    def _apply_precision_filters(candidates: List[Tuple[str, Dict]], 
                                context: QueryContext) -> List[Dict]:
        """Apply metadata + similarity filters"""
        # In production: use QueryPrecisionLayer
        return [
            {
                "text": text,
                "metadata": meta,
                "similarity_score": 0.85,
                "rank": 1
            }
            for text, meta in candidates
        ]
    
    # ========================================================================
    # MONITORING & REPORTING
    # ========================================================================
    
    def get_system_status(self) -> Dict:
        """Get complete system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "ingestion_state": self.ingestion_state,
            "monitoring": self.monitor.get_current_status()["summary"],
            "routing_stats": self.router.get_routing_stats(),
            "log_stats": self.logger_structured.get_statistics()
        }
    
    def save_full_report(self) -> Dict:
        """Save comprehensive report"""
        
        # Save monitoring report
        monitor_report = self.monitor.save_status_report()
        
        # Save logs
        log_file = self.logger_structured.save_logs(format="json")
        
        # Save validation logs
        validation_file = self.validator.save_validation_log(format="json")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "monitoring_report": str(monitor_report),
            "logs_file": str(log_file),
            "validation_file": str(validation_file),
            "system_status": self.get_system_status()
        }
        
        # Save report
        report_file = self.config_dir / "system_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Full report saved: {report_file}")
        
        return report


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print(r"""
    🚀 NEURONIX POST-INGESTION SYSTEM
    ==================================
    
    Integrated Pipeline:
    1. Metadata attachment
    2. Semantic cleanup
    3. Checkpoint validation
    4. Query precision layer
    5. Monitoring & logging
    6. Hybrid routing
    
    Usage:
    
    from integration_system import NeuronixPostIngestionSystem
    
    # Initialize
    system = NeuronixPostIngestionSystem()
    
    # Ingest PDF
    result = system.ingest_pdf_with_metadata(
        pdf_path="dsm5.pdf",
        batch_id="batch_001",
        domain_tags=["psychiatric", "diagnostic"],
        chapter=2,
        section="Depressive Disorders"
    )
    
    # Execute query
    query_result = system.execute_precision_query(
        query="What is anxiety?",
        domain_filters=["psychiatric"],
        user_difficulty="beginner"
    )
    
    # Get status
    status = system.get_system_status()
    
    # Save report
    report = system.save_full_report()
    """)
