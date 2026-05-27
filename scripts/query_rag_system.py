"""
Neuronix RAG Query System (Production Grade)
=============================================
Query the vector database with HuggingFace embeddings for semantic search 
and answer generation with Hinglish tone + clinical safety.

Features:
- HuggingFace embeddings (sentence-transformers/all-MiniLM-L6-v2) - SAME as ingestion
- Retrieve 5-8 most relevant chunks from ChromaDB
- Crisis detection with immediate helplines
- Hinglish tone for friendly, relatable responses
- Answers from context using Gemini
- Auto-append clinical disclaimer + resources
- Country-aware clinical standards (DSM-5/ICD-11/Hybrid)
"""

import sys
import os
import json
import logging
import time
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

# Import RAG Enhancements (reranking, multi-query, compression)
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag_enhancements import EnhancedRAGRetrieval, create_rag_prompt

# Import Advanced RAG Features (hybrid search, caching, metadata filtering)
from rag_advanced import AdvancedRAGRetriever

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration - SAME as ingestion pipeline
BASE_DIR = Path(__file__).parent.parent
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
    
    def __init__(self, num_chunks: int = DEFAULT_CHUNKS, country: str = "India"):
        """
        Initialize the query system
        
        Args:
            num_chunks: Number of chunks to retrieve (5-8 recommended)
            country: User's country for standard routing and resources
        """
        logger.info("\n" + "="*80)
        logger.info("🧠 NEURONIX RAG QUERY SYSTEM - INITIALIZING")
        logger.info("="*80)
        
        self.country = country
        self.num_chunks = max(MIN_CHUNKS, min(num_chunks, MAX_CHUNKS))
        
        logger.info(f"   Embedding Model: {EMBEDDING_MODEL}")
        logger.info(f"   Chunks to retrieve: {self.num_chunks}")
        logger.info(f"   Country: {country}")
        logger.info("="*80 + "\n")
        
        # Lazy load dependencies
        try:
            from langchain_chroma import Chroma
            self.Chroma = Chroma
        except ImportError as e:
            logger.error(f"❌ Failed to import ChromaDB: {e}")
            raise
        
        # Initialize HuggingFace embeddings - SAME MODEL AS INGESTION
        try:
            logger.info(f"📦 Loading HuggingFace embeddings: {EMBEDDING_MODEL}...")
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            logger.info(f"✅ HuggingFace Embeddings ready ({EMBEDDING_DIMENSIONS}-dim)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            raise
        
        # Load vector store
        try:
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
                logger.info(f"✅ Vector store loaded ({db_status['documents_count']:,} documents)")
        except Exception as e:
            logger.error(f"❌ Failed to load vector store: {e}")
            raise
        
        # Initialize LLM for answer generation (optional - falls back to context)
        self.llm = None
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info(f"🤖 Initializing Gemini LLM for answer generation...")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=0.7,
                top_p=0.8,
                top_k=40
            )
            logger.info(f"✅ Gemini LLM ready")
        except Exception as e:
            logger.warning(f"⚠️  LLM initialization failed: {e} - Will use context-only responses")
        
        # Initialize clinical formatter for safety + tone
        self.clinical_formatter = None
        if CLINICAL_FORMATTER_AVAILABLE:
            try:
                self.clinical_formatter = ClinicalResponseFormatter()
                logger.info(f"✅ Clinical safety formatter initialized")
            except Exception as e:
                logger.warning(f"⚠️  Clinical formatter init failed: {e}")
        
        # Initialize Enhanced Retriever (reranking, multi-query, compression)
        try:
            logger.info(f"🚀 Initializing Enhanced Retrieval (reranking + multi-query)...")
            self.enhanced_retriever = EnhancedRAGRetrieval(
                self.vector_store,
                verbose=False
            )
            logger.info(f"✅ Enhanced Retrieval ready")
        except Exception as e:
            logger.warning(f"⚠️  Enhanced retrieval failed: {e}")
            self.enhanced_retriever = None
        
        # Initialize Advanced RAG Retriever (hybrid search + caching + metadata filtering)
        try:
            logger.info(f"🎯 Initializing Advanced RAG (Hybrid + Cache)...")
            self.advanced_retriever = AdvancedRAGRetriever(
                vector_store=self.vector_store,
                enable_hybrid=True,        # Semantic + keyword search
                enable_cache=True,         # LRU query caching
                enable_reranking=False,    # Disabled (adds 50-200ms overhead)
                hybrid_alpha=0.6,          # 60% semantic, 40% keyword
                cache_size=200             # Store up to 200 queries
            )
            logger.info(f"✅ Advanced RAG ready (Hybrid + Cache enabled)")
        except Exception as e:
            logger.warning(f"⚠️  Advanced RAG initialization failed: {e}")
            self.advanced_retriever = None
        
        # Load mapping for metadata
        self.mapping_data = self._load_mapping()
        
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
        Uses Advanced RAG with hybrid search (semantic + keyword) and query caching
        
        Args:
            query: User question/query
            k: Number of chunks to retrieve (uses self.num_chunks if None)
            
        Returns:
            List of Document objects with metadata
        """
        k = k or self.num_chunks
        k = max(MIN_CHUNKS, min(k, MAX_CHUNKS))  # Enforce bounds
        
        try:
            logger.info(f"🔍 Searching for: '{query}'")
            logger.info(f"   Retrieving {k} chunks...")
            
            start_time = time.time()
            
            # Use Advanced RAG Retriever (hybrid + cache optimizations)
            if self.advanced_retriever:
                results = self.advanced_retriever.retrieve(query, k=k)
                
                # Log cache performance if available
                try:
                    stats = self.advanced_retriever.get_stats()
                    cache_stats = stats.get('cache', {})
                    if cache_stats:
                        cache_hit_rate = cache_stats.get('hit_rate_percent', 0)
                        if cache_hit_rate > 0:
                            logger.info(f"   💾 Cache HIT ({cache_hit_rate:.1f}%)")
                except Exception:
                    pass  # Stats not available, continue normally
            else:
                # Fallback: Use basic similarity search
                logger.info(f"   Using basic search (advanced retriever unavailable)")
                results = self.vector_store.similarity_search(query, k=k)
            
            search_time = time.time() - start_time
            
            logger.info(f"✅ Found {len(results)} relevant chunks ({search_time:.2f}s)\n")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during retrieval: {e}")
            # Fallback to basic search
            try:
                return self.vector_store.similarity_search(query, k=k)
            except:
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

QUESTION: {query}

CONTEXT FROM TEXTBOOKS:
{context_str}

ANSWER (Be helpful, cite sources, keep it simple):"""
                
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
            else:
                # Fallback: format context with answer guidance
                answer = self._format_context_only(query, context)
            
            # Add citations
            sources = list(set([doc.metadata.get('source_file', 'Unknown') for doc in context]))
            citations = f"\n\n📚 Sources:\n" + "\n".join([f"   • {src}" for src in sources])
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
        result = f"📌 Relevant Information for: '{query}'\n\n"
        
        for i, doc in enumerate(context, 1):
            source = doc.metadata.get('source_file', 'Unknown')
            page = doc.metadata.get('page', '?')
            content = doc.page_content[:250]
            result += f"[{i}] {source} (Page {page})\n    {content}...\n\n"
        
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
        logger.info("\n" + "="*80)
        logger.info("📤 NEURONIX RAG QUERY")
        logger.info("="*80)
        logger.info(f"Query: {query}\n")
        
        num_chunks = num_chunks or self.num_chunks
        
        # Check for crisis first (immediate routing)
        if self._is_crisis_query(query):
            logger.info("🚨 Crisis query detected - routing to immediate support\n")
            return self.clinical_formatter._route_crisis(self.country)
        
        # Retrieve context (5-8 chunks)
        context = self.retrieve_context(query, k=num_chunks)
        
        # Generate answer from context
        answer = self.generate_answer(query, context)
        
        logger.info("="*80)
        logger.info("✅ RAG QUERY COMPLETE\n")
        
        return answer
    
    def batch_query(self, queries: List[str]) -> List[Tuple[str, str]]:
        """
        Process multiple queries
        
        Args:
            queries: List of questions
            
        Returns:
            List of (query, answer) tuples
        """
        results = []
        for i, query in enumerate(queries, 1):
            logger.info(f"\n🔄 Query {i}/{len(queries)}")
            answer = self.query(query)
            results.append((query, answer))
        return results


def interactive_mode(country: str = "India", num_chunks: int = DEFAULT_CHUNKS):
    """Run interactive query mode"""
    import sys
    
    try:
        system = NeuronixRAGQuerySystem(num_chunks=num_chunks, country=country)
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("🧠 NEURONIX RAG QUERY SYSTEM - INTERACTIVE MODE")
    print("="*80)
    print(f"Country: {country}")
    print(f"Chunks per query: {num_chunks}")
    print("\nType 'exit' to quit, 'chunks N' to change chunks (5-8), 'country NAME' to change country")
    print("="*80 + "\n")
    
    while True:
        try:
            query = input("🤔 Ask a question: ").strip()
            
            if query.lower() == 'exit':
                print("\nGoodbye! 👋\n")
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
            print("\n\nGoodbye! 👋\n")
            break
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            continue
    
    def query(self, question: str, k: int = 5, generate_answer: bool = True) -> Dict:
        """
        Complete RAG query pipeline
        
        Args:
            question: User question
            k: Number of context documents to retrieve
            generate_answer: Whether to generate LLM answer or just return context
            
        Returns:
            Dictionary with retrieved_docs, answer, and metadata
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"QUERY: {question}")
        logger.info(f"{'='*70}\n")
        
        # Retrieve context
        retrieved_docs = self.retrieve_context(question, k=k)
        
        if not retrieved_docs:
            logger.warning("No documents retrieved")
            return {
                "query": question,
                "documents": [],
                "answer": "Sorry, I couldn't find relevant information in the database.",
                "metadata": {
                    "documents_retrieved": 0,
                    "database_status": self.check_database_status()
                }
            }
        
        # Generate answer if requested
        answer = ""
        if generate_answer:
            answer = self.generate_answer(question, retrieved_docs)
            logger.info("📝 ANSWER:")
            logger.info(answer)
        
        # Format output
        return {
            "query": question,
            "documents": [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get('source', 'unknown'),
                    "country": doc.metadata.get('country', 'unknown'),
                    "page": doc.metadata.get('page', 'unknown')
                }
                for doc in retrieved_docs
            ],
            "answer": answer,
            "metadata": {
                "documents_retrieved": len(retrieved_docs),
                "database_status": self.check_database_status()
            }
        }


def interactive_query_mode():
    """Run interactive query interface"""
    print("\n" + "="*70)
    print("🧠 NEURONIX RAG QUERY SYSTEM")
    print("="*70)
    print("\nInitializing system...\n")
    
    try:
        system = NeuronixRAGQuerySystem()
    except Exception as e:
        print(f"\n❌ Failed to initialize query system: {e}")
        print("\n⚠️  Make sure:")
        print("   1. Vector database is populated (run: python scripts/ingest_data.py)")
        print("   2. GOOGLE_API_KEY environment variable is set")
        return
    
    # Check database status
    db_status = system.check_database_status()
    print(f"\n📦 Vector Database Status:")
    print(f"   Location: {db_status['location']}")
    print(f"   Documents: {db_status['documents_count']}")
    print(f"   Status: {'✅ Ready' if db_status['ready'] else '❌ Empty or Error'}\n")
    
    if not db_status['ready']:
        print("⚠️  Database appears empty. Running ingestion...")
        print("   Execute: python scripts/ingest_data.py\n")
        return
    
    print("💡 Ask questions about psychology, clinical concepts, etc.")
    print("   Type 'quit' to exit\n")
    print("="*70 + "\n")
    
    while True:
        try:
            question = input("❓ Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for using Neuronix RAG!")
                break
            
            if not question:
                print("Please enter a question.\n")
                continue
            
            # Process query
            result = system.query(question, k=5, generate_answer=True)
            
            print("\n" + "="*70 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")


def test_query_system():
    """Test the query system with sample questions"""
    print("\n" + "="*70)
    print("🧪 TESTING RAG QUERY SYSTEM")
    print("="*70 + "\n")
    
    try:
        system = NeuronixRAGQuerySystem()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test queries
    test_questions = [
        "What is cognitive psychology?",
        "depression treatment options",
        "How does CBT work?",
        "abnormal psychology overview"
    ]
    
    print(f"\n📦 Database: {system.check_database_status()['documents_count']} documents\n")
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(test_questions)}")
        print(f"{'='*70}")
        
        result = system.query(question, k=3, generate_answer=False)
        
        print(f"\nDocuments Retrieved: {result['metadata']['documents_retrieved']}")
        if result['documents']:
            for j, doc in enumerate(result['documents'], 1):
                print(f"\n  [{j}] {doc['source']} ({doc['country']})")
                print(f"      {doc['content'][:150]}...")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_query_system()
        elif sys.argv[1] == 'interactive':
            interactive_query_mode()
        else:
            print("Usage:")
            print("  python query_rag_system.py                (interactive mode)")
            print("  python query_rag_system.py test           (run tests)")
            print("  python query_rag_system.py interactive    (interactive mode)")
    else:
        interactive_query_mode()
