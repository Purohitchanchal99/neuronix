"""
🔧 POST-INGESTION OPTIMIZATION LAYER FOR NEURONIX
====================================================
Handles metadata, semantic cleanup, validation, and precision queries
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import hashlib
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 1️⃣ METADATA SCHEMA
# ============================================================================

class DomainTag(Enum):
    """Clinical domain tags"""
    PSYCHIATRIC = "psychiatric"
    NEUROLOGICAL = "neurological"
    PSYCHOLOGICAL = "psychological"
    PHARMACOLOGICAL = "pharmacological"
    THERAPEUTIC = "therapeutic"
    DIAGNOSTIC = "diagnostic"
    EPIDEMIOLOGICAL = "epidemiological"
    LIFESTYLE = "lifestyle"


@dataclass
class ChunkMetadata:
    """Metadata schema for each chunk"""
    
    # Source information
    source_pdf: str  # PDF filename
    source_url: str  # Original URL
    
    # Location in document
    chapter: int  # Chapter number
    section: str  # Section title
    subsection: Optional[str] = None
    
    # Content classification
    domain_tags: List[str]  # Multiple domain tags
    difficulty_level: str  # beginner/intermediate/advanced
    
    # Clinical specifications
    dsm5_reference: Optional[str] = None  # e.g., "F32.9 - Major Depressive Disorder"
    icd11_reference: Optional[str] = None  # e.g., "6M82 - Depressive Disorder"
    
    # Language & quality
    language: str = "en"  # en, hi, hinglish
    quality_score: float = 0.8  # 0-1, higher is better
    
    # Tracking
    ingestion_date: str = None
    chunk_id: str = None  # Unique identifier
    original_index: int = None  # Position in PDF
    
    # Content summary
    key_terms: List[str] = None  # Important keywords
    content_type: str = "text"  # text, table, figure, equation
    
    def __post_init__(self):
        if self.ingestion_date is None:
            self.ingestion_date = datetime.now().isoformat()
        if self.key_terms is None:
            self.key_terms = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'ChunkMetadata':
        """Create from dictionary"""
        # Handle datetime conversion
        if isinstance(data.get('ingestion_date'), str):
            data['ingestion_date'] = data['ingestion_date']
        return ChunkMetadata(**data)


class MetadataManager:
    """Manages metadata attachment and filtering"""
    
    def __init__(self, storage_dir: str = "metadata_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        logger.info(f"✅ MetadataManager initialized: {storage_dir}")
    
    def attach_metadata(self, chunk_text: str, **kwargs) -> ChunkMetadata:
        """
        Attach metadata to a chunk
        
        Usage:
        metadata = manager.attach_metadata(
            chunk_text,
            source_pdf="dsm5.pdf",
            chapter=2,
            section="Depressive Disorders",
            domain_tags=["psychiatric", "diagnostic"],
            dsm5_reference="F32.9"
        )
        """
        
        # Generate unique chunk ID
        chunk_id = self._generate_chunk_id(chunk_text)
        
        # Create metadata object
        metadata = ChunkMetadata(
            source_pdf=kwargs.get('source_pdf', ''),
            source_url=kwargs.get('source_url', ''),
            chapter=kwargs.get('chapter', 1),
            section=kwargs.get('section', ''),
            subsection=kwargs.get('subsection', None),
            domain_tags=kwargs.get('domain_tags', []),
            difficulty_level=kwargs.get('difficulty_level', 'intermediate'),
            dsm5_reference=kwargs.get('dsm5_reference', None),
            icd11_reference=kwargs.get('icd11_reference', None),
            language=kwargs.get('language', 'en'),
            quality_score=kwargs.get('quality_score', 0.8),
            chunk_id=chunk_id,
            original_index=kwargs.get('original_index', 0),
            key_terms=kwargs.get('key_terms', []),
            content_type=kwargs.get('content_type', 'text')
        )
        
        return metadata
    
    def save_metadata(self, chunk_id: str, metadata: ChunkMetadata):
        """Save metadata to disk"""
        file_path = self.storage_dir / f"{chunk_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
    
    def load_metadata(self, chunk_id: str) -> Optional[ChunkMetadata]:
        """Load metadata from disk"""
        file_path = self.storage_dir / f"{chunk_id}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ChunkMetadata.from_dict(data)
        return None
    
    def filter_by_metadata(self, chunks_with_metadata: List[Tuple[str, ChunkMetadata]], 
                          filters: Dict) -> List[Tuple[str, ChunkMetadata]]:
        """
        Filter chunks based on metadata criteria
        
        Example:
        filters = {
            "domain_tags": ["psychiatric", "diagnostic"],
            "chapter": 2,
            "difficulty_level": "intermediate"
        }
        """
        filtered = []
        
        for chunk, metadata in chunks_with_metadata:
            matches = True
            
            # Check domain tags
            if "domain_tags" in filters:
                query_tags = filters["domain_tags"]
                if not any(tag in metadata.domain_tags for tag in query_tags):
                    matches = False
            
            # Check chapter
            if "chapter" in filters and metadata.chapter != filters["chapter"]:
                matches = False
            
            # Check difficulty
            if "difficulty_level" in filters and metadata.difficulty_level != filters["difficulty_level"]:
                matches = False
            
            # Check DSM-5 reference
            if "dsm5_reference" in filters:
                if not metadata.dsm5_reference:
                    matches = False
                elif filters["dsm5_reference"] not in metadata.dsm5_reference:
                    matches = False
            
            # Check quality score
            if "min_quality" in filters:
                if metadata.quality_score < filters["min_quality"]:
                    matches = False
            
            if matches:
                filtered.append((chunk, metadata))
        
        return filtered
    
    @staticmethod
    def _generate_chunk_id(text: str) -> str:
        """Generate unique chunk ID"""
        return hashlib.md5(text.encode()).hexdigest()[:16]


# ============================================================================
# 2️⃣ SEMANTIC CLEANUP
# ============================================================================

class SemanticCleanupManager:
    """Handles Hinglish, misspellings, normalization"""
    
    def __init__(self):
        self.normalization_dict = self._build_normalization_dict()
        self.intent_mapping = self._build_intent_mapping()
        logger.info("✅ SemanticCleanupManager initialized")
    
    @staticmethod
    def _build_normalization_dict() -> Dict[str, str]:
        """
        Normalization dictionary for Hinglish & common misspellings
        """
        return {
            # Hinglish medical terms
            "depression": ["depression", "depresion", "diprashun", "udaasi"],
            "anxiety": ["anxiety", "anxeity", "tensions", "ghbrahaat"],
            "stress": ["stress", "stres", "tanav"],
            "sleep": ["sleep", "slep", "nind", "sutti"],
            "medication": ["medication", "medicine", "dawai", "dawa"],
            "therapy": ["therapy", "theapy", "chikitsaa"],
            "psychiatrist": ["psychiatrist", "psych", "maan-rogi-doctor"],
            "psychologist": ["psychologist", "psycholgy", "manovigyanik"],
            "symptom": ["symptom", "sympton", "lakshan"],
            "bipolar": ["bipolar", "bipolar disorder", "do-haal", "unmad"],
            "schizophrenia": ["schizophrenia", "schizofrenia", "unmada"],
            
            # Common misspellings
            "disorder": ["disorder", "dissorder", "diorder"],
            "diagnose": ["diagnose", "diagnos", "diagnos"],
            "treatment": ["treatment", "treatmnt", "treament"],
            "cognitive": ["cognitive", "cognative", "cagnitive"],
            "behavioral": ["behavioral", "behaioral", "behavirol"],
            
            # Clinical abbreviations
            "dsm5": ["dsm5", "dsm-5", "dsm 5", "dsm"],
            "icd11": ["icd11", "icd-11", "icd 11", "icd"],
            "cbt": ["cbt", "cognitive behavioral therapy", "soch badlao therapy"],
            "ssri": ["ssri", "selective serotonin reuptake inhibitor"],
        }
    
    @staticmethod
    def _build_intent_mapping() -> Dict[str, str]:
        """
        Map colloquial phrases to clinical terms
        """
        return {
            # Hinglish colloquial to clinical
            "tension ho rahi hai": "experiencing anxiety symptoms",
            "mood bilkul downgrade hai": "depressive mood",
            "neend nahi aa rahi": "experiencing insomnia",
            "chinta mein hoon": "experiencing worry and anxiety",
            "ghbrahaat ho rahi hai": "experiencing anxious symptoms",
            "udaasi aa gai": "experiencing depressive episode",
            "har cheez mein mazza nahi": "anhedonia",
            "concentration nahi ho pa rahi": "concentration difficulties",
            "sharir mein energy nahi": "fatigue and low energy",
            
            # English colloquial to clinical
            "feeling down": "experiencing depression",
            "feeling worried all the time": "generalized anxiety",
            "can't sleep": "insomnia",
            "heart racing": "tachycardia / anxiety symptom",
            "mind all over the place": "racing thoughts",
            "everything feels hopeless": "hopelessness with depressive mood",
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text using dictionary"""
        text_lower = text.lower()
        
        for canonical, variants in self.normalization_dict.items():
            for variant in variants:
                if variant in text_lower:
                    # Replace with canonical form
                    text_lower = text_lower.replace(variant, canonical)
        
        return text_lower
    
    def map_intent(self, query: str) -> str:
        """Map colloquial phrases to clinical terms"""
        query_lower = query.lower()
        
        for colloquial, clinical in self.intent_mapping.items():
            if colloquial in query_lower:
                query_lower = query_lower.replace(colloquial, clinical)
        
        return query_lower
    
    def fuzzy_match(self, input_term: str, candidates: List[str], 
                   threshold: float = 0.8) -> Optional[str]:
        """
        Fuzzy matching for noisy inputs
        Returns best match if similarity > threshold
        """
        from difflib import SequenceMatcher
        
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            score = SequenceMatcher(None, input_term.lower(), candidate.lower()).ratio()
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match if best_score >= threshold else None
    
    def clean_query(self, query: str) -> Dict:
        """
        Complete query cleaning pipeline
        Returns: original, normalized, intent-mapped, cleaned versions
        """
        original = query
        normalized = self.normalize_text(query)
        intent_mapped = self.map_intent(normalized)
        
        # Final cleanup (remove extra spaces)
        cleaned = ' '.join(intent_mapped.split())
        
        return {
            "original": original,
            "normalized": normalized,
            "intent_mapped": intent_mapped,
            "cleaned": cleaned
        }


# ============================================================================
# 3️⃣ CHECKPOINT VALIDATION
# ============================================================================

class CheckpointValidator:
    """Validates batches, logs errors, ensures data integrity"""
    
    def __init__(self, logs_dir: str = "validation_logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self.validation_log = []
        logger.info(f"✅ CheckpointValidator initialized: {logs_dir}")
    
    def validate_batch(self, batch_info: Dict) -> Dict:
        """
        Validate a batch of ingested data
        
        Example:
        batch_info = {
            "batch_id": "batch_001",
            "expected_chunks": 100,
            "actual_chunks": 100,
            "expected_embeddings": 100,
            "actual_embeddings": 100,
            "errors": [],
            "pdf_file": "dsm5.pdf"
        }
        """
        
        validation_result = {
            "batch_id": batch_info.get("batch_id"),
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
        # Check chunk count
        expected = batch_info.get("expected_chunks", 0)
        actual = batch_info.get("actual_chunks", 0)
        
        if actual == expected:
            validation_result["summary"]["chunk_count"] = "✅ PASS"
        else:
            validation_result["summary"]["chunk_count"] = f"⚠️ MISMATCH: Expected {expected}, Got {actual}"
            validation_result["errors"].append(f"Chunk count mismatch: {actual}/{expected}")
        
        # Check embeddings
        expected_emb = batch_info.get("expected_embeddings", 0)
        actual_emb = batch_info.get("actual_embeddings", 0)
        
        if actual_emb == expected_emb:
            validation_result["summary"]["embeddings"] = "✅ PASS"
        else:
            validation_result["summary"]["embeddings"] = f"⚠️ MISMATCH: Expected {expected_emb}, Got {actual_emb}"
            validation_result["errors"].append(f"Embedding count mismatch: {actual_emb}/{expected_emb}")
        
        # Check for corrupted PDFs
        if batch_info.get("errors"):
            validation_result["warnings"].append(f"Found errors: {batch_info['errors']}")
        
        # Determine overall status
        if not validation_result["errors"]:
            validation_result["status"] = "✅ PASS"
        else:
            validation_result["status"] = "❌ FAIL"
        
        # Log the validation
        self.validation_log.append(validation_result)
        
        return validation_result
    
    def save_validation_log(self, format: str = "json"):
        """
        Save validation log to disk
        format: json, csv
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            log_file = self.logs_dir / f"validation_{timestamp}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.validation_log, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            import csv
            log_file = self.logs_dir / f"validation_{timestamp}.csv"
            
            if self.validation_log:
                with open(log_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.validation_log[0].keys())
                    writer.writeheader()
                    writer.writerows(self.validation_log)
        
        logger.info(f"✅ Validation log saved: {log_file}")
        return log_file
    
    def get_validation_summary(self) -> Dict:
        """Get summary of all validations"""
        total = len(self.validation_log)
        passed = sum(1 for v in self.validation_log if v["status"] == "✅ PASS")
        failed = sum(1 for v in self.validation_log if v["status"] == "❌ FAIL")
        
        return {
            "total_batches": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "errors": [e for v in self.validation_log for e in v.get("errors", [])]
        }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example 1: Metadata attachment
    print("\n1️⃣ Metadata Attachment Example:")
    metadata_mgr = MetadataManager()
    
    chunk_text = "Depression is a mood disorder characterized by persistent sad mood..."
    metadata = metadata_mgr.attach_metadata(
        chunk_text,
        source_pdf="dsm5.pdf",
        chapter=2,
        section="Depressive Disorders",
        domain_tags=["psychiatric", "diagnostic"],
        difficulty_level="intermediate",
        dsm5_reference="F32.9 - Major Depressive Disorder",
        key_terms=["depression", "mood disorder", "persistent sadness"]
    )
    
    print(f"✅ Chunk ID: {metadata.chunk_id}")
    print(f"✅ Domain Tags: {metadata.domain_tags}")
    
    # Example 2: Semantic cleanup
    print("\n2️⃣ Semantic Cleanup Example:")
    cleanup_mgr = SemanticCleanupManager()
    
    queries = [
        "tension ho rahi hai",
        "depresion treatment ke liye kya karna chahiye",
        "anxiety and stress management"
    ]
    
    for q in queries:
        cleaned = cleanup_mgr.clean_query(q)
        print(f"Original: {cleaned['original']}")
        print(f"Cleaned: {cleaned['cleaned']}\n")
    
    # Example 3: Checkpoint validation
    print("\n3️⃣ Checkpoint Validation Example:")
    validator = CheckpointValidator()
    
    batch_info = {
        "batch_id": "batch_001",
        "expected_chunks": 100,
        "actual_chunks": 100,
        "expected_embeddings": 100,
        "actual_embeddings": 100,
        "errors": [],
        "pdf_file": "dsm5.pdf"
    }
    
    result = validator.validate_batch(batch_info)
    print(f"Status: {result['status']}")
    print(f"Summary: {result['summary']}")
