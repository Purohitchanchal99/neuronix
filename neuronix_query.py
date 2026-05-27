"""
Neuronix RAG Query Script (Production Grade)
=============================================
Query the vector database with HuggingFace embeddings for semantic search 
and answer generation with Hinglish tone + clinical safety.

🎯 Specifications:
- Use SAME HuggingFace embeddings as ingestion (all-MiniLM-L6-v2)
- Retrieve 5-8 chunks from ChromaDB
- Generate answers using Gemini from context
- Apply Hinglish tone (clear, helpful, not formal)
- Crisis detection with immediate helplines
- Auto-append disclaimer + country resources

Features:
✅ HuggingFace embeddings (sentence-transformers/all-MiniLM-L6-v2) - SAME as ingestion
✅ Retrieve 5-8 most relevant chunks from ChromaDB
✅ Crisis detection with immediate helplines
✅ Hinglish tone for friendly, relatable responses
✅ Answers primarily from context using Gemini
✅ Auto-append clinical disclaimer + resources
✅ Country-aware clinical standards (DSM-5/ICD-11/Hybrid)
✅ Full monitoring and logging

Usage:
    # Interactive mode
    python neuronix_query.py

    # Single query
    python neuronix_query.py "depression treatment options"

    # With custom chunks (5-8 range)
    python neuronix_query.py "anxiety disorders" --chunks 7

    # Different country
    python neuronix_query.py --country USA
"""

import sys
import os
import json
import logging
import time
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Windows compatibility  
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

# LangChain imports
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables (HF_TOKEN, GOOGLE_API_KEY, etc)
from dotenv import load_dotenv
load_dotenv()

# Import RAG Enhancements (reranking, multi-query, compression)
sys.path.insert(0, str(Path(__file__).parent))
from rag_enhancements import EnhancedRAGRetrieval, create_rag_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIGURATION - MUST MATCH INGESTION PIPELINE
# ================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
MAPPING_FILE = DATA_DIR / "master_mapping.json"

# Embedding model - MUST MATCH INGESTION
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

# Query configuration
MIN_CHUNKS = 5
MAX_CHUNKS = 8
DEFAULT_CHUNKS = 6

# Import clinical response formatter for safety + tone
try:
    from clinical_response_formatter import ClinicalResponseFormatter
    CLINICAL_FORMATTER_AVAILABLE = True
except:
    CLINICAL_FORMATTER_AVAILABLE = False
    logger.warning("⚠️  Clinical formatter not available - using basic responses")


class NeuronixRAGQuerySystem:
    """Production-grade RAG query system with clinical safety"""
    
    def __init__(self, num_chunks: int = DEFAULT_CHUNKS, country: str = "India", verbose: bool = True):
        """
        Initialize the query system
        
        Args:
            num_chunks: Number of chunks to retrieve (5-8 recommended)
            country: User's country for standard routing and resources
            verbose: Enable detailed logging
        """
        self.verbose = verbose
        self.country = country
        self.num_chunks = max(MIN_CHUNKS, min(num_chunks, MAX_CHUNKS))
        self.query_count = 0
        
        if self.verbose:
            logger.info("\n" + "="*80)
            logger.info("🧠 NEURONIX RAG QUERY SYSTEM - INITIALIZING")
            logger.info("="*80)
            logger.info(f"   Embedding Model: {EMBEDDING_MODEL}")
            logger.info(f"   Chunks to retrieve: {self.num_chunks}")
            logger.info(f"   Country: {country}")
            logger.info("="*80)
        
        # Lazy load dependencies
        try:
            from langchain_chroma import Chroma
            self.Chroma = Chroma
        except ImportError as e:
            logger.error(f"❌ Failed to import ChromaDB: {e}")
            raise
        
        # Initialize HuggingFace embeddings - SAME MODEL AS INGESTION
        try:
            if self.verbose:
                logger.info(f"📦 Loading HuggingFace embeddings: {EMBEDDING_MODEL}...")
                logger.info(f"   Using cache folder: ./hf_cache")
            
            # Create cache folder if it doesn't exist
            cache_folder = BASE_DIR / "hf_cache"
            cache_folder.mkdir(parents=True, exist_ok=True)
            
            # Initialize with caching to avoid repeated downloads
            # HF_TOKEN is loaded from .env automatically
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                cache_folder=str(cache_folder),
                model_kwargs={"trust_remote_code": True}
            )
            if self.verbose:
                logger.info(f"✅ HuggingFace Embeddings ready ({EMBEDDING_DIMENSIONS}-dim)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            raise
        
        # Load vector store
        try:
            if self.verbose:
                logger.info(f"🗄️  Loading ChromaDB vector store...")
            self.vector_store = self.Chroma(
                collection_name="neuronix_medical_kb",
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=self.embeddings
            )
            
            # Verify database is populated
            db_status = self.check_database_status()
            if not db_status['ready']:
                logger.warning(f"⚠️  Vector database appears empty or not ready")
            else:
                if self.verbose:
                    logger.info(f"✅ Vector store loaded ({db_status['documents_count']:,} documents)")
        except Exception as e:
            logger.error(f"❌ Failed to load vector store: {e}")
            raise
        
        # Initialize LLM for answer generation (optional - falls back to context)
        self.llm = None
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            if self.verbose:
                logger.info(f"🤖 Initializing Gemini LLM for answer generation...")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.7,
                top_p=0.8,
                top_k=40
            )
            if self.verbose:
                logger.info(f"✅ Gemini LLM ready")
        except Exception as e:
            if self.verbose:
                logger.warning(f"⚠️  LLM initialization failed: {e} - Will use context-only responses")
        
        # Initialize clinical formatter for safety + tone
        self.clinical_formatter = None
        if CLINICAL_FORMATTER_AVAILABLE:
            try:
                self.clinical_formatter = ClinicalResponseFormatter()
                if self.verbose:
                    logger.info(f"✅ Clinical safety formatter initialized")
            except Exception as e:
                if self.verbose:
                    logger.warning(f"⚠️  Clinical formatter init failed: {e}")
        
        # Initialize Enhanced Retriever (reranking, multi-query, compression)
        try:
            if self.verbose:
                logger.info(f"🚀 Initializing Enhanced Retrieval (reranking + multi-query)...")
            self.enhanced_retriever = EnhancedRAGRetrieval(
                self.vector_store,
                verbose=False
            )
            if self.verbose:
                logger.info(f"✅ Enhanced Retrieval ready")
        except Exception as e:
            logger.warning(f"⚠️  Enhanced retrieval failed: {e}")
            self.enhanced_retriever = None
        
        # Load mapping for metadata
        self.mapping_data = self._load_mapping()
        
        if self.verbose:
            logger.info("✅ Neuronix RAG Query System ready for queries!\n")
    
    def _load_mapping(self) -> Dict:
        """Load the master_mapping.json for metadata"""
        try:
            with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️  Could not load mapping: {e}")
            return {}
    
    def check_database_status(self) -> Dict:
        """Check if vector database is populated"""
        try:
            count_result = self.vector_store._collection.count()
            return {
                "status": "active",
                "documents_count": count_result,
                "ready": count_result > 0,
                "location": str(VECTOR_DB_DIR)
            }
        except Exception as e:
            logger.warning(f"⚠️  Could not determine database status: {e}")
            return {
                "status": "unknown",
                "documents_count": 0,
                "ready": False,
                "location": str(VECTOR_DB_DIR),
                "error": str(e)
            }
    
    def retrieve_context(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieve top-k most relevant chunks from vector store
        Uses ENHANCED retrieval with reranking and multi-query generation
        
        Args:
            query: User question/query
            k: Number of chunks to retrieve (uses self.num_chunks if None)
            
        Returns:
            List of Document objects with metadata
        """
        k = k or self.num_chunks
        k = max(MIN_CHUNKS, min(k, MAX_CHUNKS))  # Enforce bounds
        
        try:
            if self.verbose:
                logger.info(f"🔍 Searching for: '{query}'")
                total_available = len(self.vector_store._collection.get()['ids'])
                logger.info(f"   Retrieving {k} chunks from {total_available:,} available...")
            
            # Perform ENHANCED similarity search (with reranking + multi-query)
            start_time = time.time()
            
            if self.enhanced_retriever:
                # Use enhanced retrieval (reranking + multi-query)
                results_raw = self.enhanced_retriever.retrieve_enhanced(
                    query=query,
                    k=k,
                    rerank=True,        # BM25 reranking (25-46% quality improvement)
                    compress=False,      # Keep full context for clinical use
                    multi_query=True     # Generate query variations (15-30% better recall)
                )
                
                # Convert dict results back to Document objects
                results = []
                for r in results_raw:
                    doc = Document(
                        page_content=r['content'],
                        metadata=r.get('metadata', {})
                    )
                    results.append(doc)
            else:
                # Fallback to basic similarity search
                results = self.vector_store.similarity_search(query, k=k)
            
            search_time = time.time() - start_time
            
            if self.verbose:
                logger.info(f"✅ Found {len(results)} relevant chunks ({search_time:.2f}s)")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during retrieval: {e}")
            return []
    
    def _is_crisis_query(self, query: str) -> bool:
        """Detect if query contains crisis keywords"""
        if not self.clinical_formatter:
            return False
        return self.clinical_formatter._is_crisis_query(query)
    
    def generate_answer(self, query: str, context: List[Document]) -> str:
        """
        Generate answer using LLM with retrieved context
        Uses Hinglish tone + clinical safety
        
        Args:
            query: Original user query
            context: Retrieved documents from vector store
            
        Returns:
            Generated answer with citations and safety formatting
        """
        if not context:
            response = "Yeh information abhi mere paas complete nahi hai. Kripaya qualified professional se consult karein."
            if self.clinical_formatter:
                response = self.clinical_formatter.format_response(
                    response, query, self.country
                )
            return response
        
        try:
            # Build context string with citations
            context_str = "\n\n".join([
                f"[📚 {doc.metadata.get('source_file', 'Unknown')}]\n{doc.page_content}"
                for doc in context
            ])
            
            # Generate answer based on context
            if self.llm:
                # Use LLM if available
                prompt = f"""You are a helpful psychology/mental health education assistant speaking to someone from India.

Based on the following textbook excerpts, answer the user's question.
Be concise, accurate, and cite your sources.
Use simple, friendly language (can mix Hindi/English - Hinglish is fine).
Focus on answering from the provided context.

QUESTION: {query}

CONTEXT FROM TEXTBOOKS:
{context_str}

ANSWER (Be helpful, cite sources, keep it simple):"""
                
                if self.verbose:
                    logger.info("📝 Generating answer with Gemini...")
                
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
            else:
                # Fallback: format context with answer guidance
                answer = self._format_context_only(query, context)
            
            # Add citations - mention book titles only
            sources = list(set([doc.metadata.get('source_file', 'Unknown') for doc in context]))
            citations = f"\n\n📚 Sources:\n" + "\n".join([f"   • {src}" for src in sources if src != 'Unknown'])
            answer = answer + citations
            
            # Apply clinical formatting (crisis detection, Hinglish tone, disclaimer, resources)
            if self.clinical_formatter:
                answer = self.clinical_formatter.format_response(
                    answer, query, self.country
                )
            
            return answer
            
        except Exception as e:
            logger.error(f"❌ Error generating answer: {e}")
            return self._format_context_only(query, context)
    
    def _format_context_only(self, query: str, context: List[Document]) -> str:
        """Fallback: format context without LLM"""
        result = f"📌 Information on: '{query}'\n\n"
        
        for i, doc in enumerate(context, 1):
            source = doc.metadata.get('source_file', 'Unknown')
            content = doc.page_content[:250]
            result += f"[{i}] {source}\n    {content}...\n\n"
        
        return result
    
    def query(self, query: str, num_chunks: Optional[int] = None) -> str:
        """
        Complete query pipeline:
        1. Check for crisis keywords
        2. Retrieve context (5-8 chunks)
        3. Generate answer from context
        4. Apply Hinglish tone + clinical safety
        
        Args:
            query: User question
            num_chunks: Override default chunks (5-8 range enforced)
            
        Returns:
            Complete formatted answer with sources
        """
        self.query_count += 1
        
        if self.verbose:
            logger.info("\n" + "="*80)
            logger.info(f"📤 NEURONIX RAG QUERY #{self.query_count}")
            logger.info("="*80)
            logger.info(f"Query: {query}\n")
        
        num_chunks = num_chunks or self.num_chunks
        
        # Check for crisis first (immediate routing)
        if self._is_crisis_query(query):
            if self.verbose:
                logger.info("🚨 Crisis query detected - routing to immediate support\n")
            if self.clinical_formatter:
                return self.clinical_formatter._route_crisis(self.country)
        
        # Retrieve context (5-8 chunks)
        context = self.retrieve_context(query, k=num_chunks)
        
        # Generate answer from context
        answer = self.generate_answer(query, context)
        
        if self.verbose:
            logger.info("\n" + "="*80)
            logger.info("✅ RAG QUERY COMPLETE")
            logger.info("="*80 + "\n")
        
        return answer


def interactive_mode(country: str = "India", num_chunks: int = DEFAULT_CHUNKS):
    """Run interactive query mode"""
    try:
        system = NeuronixRAGQuerySystem(num_chunks=num_chunks, country=country, verbose=True)
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("🧠 NEURONIX RAG QUERY SYSTEM - INTERACTIVE MODE")
    print("="*80)
    print(f"Country: {country}")
    print(f"Chunks per query: {num_chunks}")
    print("\nCommands:")
    print("  exit, quit, q     - Exit the system")
    print("  chunks N          - Change chunks (5-8)")
    print("  country NAME      - Change country")
    print("="*80 + "\n")
    
    while True:
        try:
            query = input("🤔 Ask a question: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Thank you for using Neuronix RAG!\n")
                break
            
            if query.lower().startswith('chunks '):
                try:
                    new_chunks = int(query.split()[1])
                    system.num_chunks = max(MIN_CHUNKS, min(new_chunks, MAX_CHUNKS))
                    print(f"✅ Chunks updated to {system.num_chunks}\n")
                    continue
                except (ValueError, IndexError):
                    print("❌ Usage: chunks 5-8\n")
                    continue
            
            if query.lower().startswith('country '):
                new_country = query.replace('country ', '').strip()
                system.country = new_country
                print(f"✅ Country updated to {new_country}\n")
                continue
            
            if not query:
                continue
            
            # Execute query
            answer = system.query(query)
            print(f"\n{answer}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            continue


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="🧠 Neuronix RAG Query System - Medical/Psychology Educational AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python neuronix_query.py                            (Interactive mode)
  python neuronix_query.py "depression causes"       (Single query)
  python neuronix_query.py "anxiety" --chunks 7      (Single query with 7 chunks)
  python neuronix_query.py --country USA             (Interactive mode for USA)
        """
    )
    
    parser.add_argument("query", nargs="?", default=None,
                       help="Question to ask (if not provided, runs interactive mode)")
    parser.add_argument("--chunks", type=int, default=DEFAULT_CHUNKS,
                       help=f"Number of chunks to retrieve ({MIN_CHUNKS}-{MAX_CHUNKS}, default: {DEFAULT_CHUNKS})")
    parser.add_argument("--country", type=str, default="India",
                       help="User's country for clinical standards (default: India)")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress detailed logging")
    
    args = parser.parse_args()
    
    # Ensure chunks are in valid range
    chunks = max(MIN_CHUNKS, min(args.chunks, MAX_CHUNKS))
    
    try:
        system = NeuronixRAGQuerySystem(
            num_chunks=chunks, 
            country=args.country,
            verbose=not args.quiet
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
        sys.exit(1)
    
    # If query provided, execute it
    if args.query:
        print(f"\n🤔 Query: {args.query}")
        answer = system.query(args.query)
        print(f"\n{answer}\n")
    # Otherwise run interactive mode
    else:
        interactive_mode(country=args.country, num_chunks=chunks)
    

if __name__ == "__main__":
    main()
