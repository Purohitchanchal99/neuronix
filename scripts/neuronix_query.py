"""
Neuronix Query System
====================
Clinical psychology RAG with HuggingFace embeddings

Features:
- HuggingFace embeddings (same model as ingestion)
- Retrieve top 5–8 chunks from ChromaDB
- Generate answers using Gemini LLM
- Fallback with Hinglish messages
- Clear citations with sources
"""

import sys
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Windows compatibility
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

from langchain_core.documents import Document
from neuronix_constants import (
    EMBEDDING_MODEL, COLLECTION_NAME, CHROMA_PERSIST_DIRECTORY,
    VECTOR_DB_DIR, CHECKPOINT_FILE, LOG_FORMAT, MAPPING_FILE,
    LLM_MODEL, LLM_TEMPERATURE, LLM_TOP_P, LLM_TOP_K,
    QUERY_DEFAULT_K, RETRIEVAL_K_MIN, RETRIEVAL_K_MAX,
    INSUFFICIENT_CONTEXT_MSG, NO_RESULTS_MSG, ERROR_MSG
)

# Import Advanced RAG Features (hybrid search + caching)
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag_advanced import AdvancedRAGRetriever

# ================================================================
# LOGGING CONFIGURATION
# ================================================================
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'neuronix_query.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NeuronixQuerySystem:
    """Clinical psychology RAG query system with HuggingFace embeddings"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize query system
        
        Args:
            verbose: Enable detailed logging
        """
        if verbose:
            logger.info("🧠 Initializing Neuronix Query System...")
        
        self.verbose = verbose
        self.llm = None
        self.vector_store = None
        self.embeddings = None
        self.advanced_retriever = None
        
        try:
            # Import dependencies
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_chroma import Chroma
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Initialize HuggingFace embeddings - CRITICAL: Same model as ingestion
            if verbose:
                logger.info(f"📦 Loading HuggingFace model: {EMBEDDING_MODEL}")
            
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"}
            )
            
            if verbose:
                logger.info(f"✅ HuggingFace Embeddings ready (384-dim)")
            
            # Load ChromaDB vector store
            if verbose:
                logger.info(f"🗄️  Loading ChromaDB vector store...")
            
            self.vector_store = Chroma(
                collection_name=COLLECTION_NAME,
                persist_directory=str(VECTOR_DB_DIR),
                embedding_function=self.embeddings
            )
            
            if verbose:
                logger.info(f"✅ ChromaDB loaded")
            
            # Initialize Gemini LLM
            try:
                if verbose:
                    logger.info(f"🤖 Initializing Gemini LLM ({LLM_MODEL})...")
                
                self.llm = ChatGoogleGenerativeAI(
                    model=LLM_MODEL,
                    temperature=LLM_TEMPERATURE,
                    top_p=LLM_TOP_P,
                    top_k=LLM_TOP_K
                )
                
                if verbose:
                    logger.info(f"✅ Gemini LLM ready")
                    
            except Exception as e:
                logger.warning(f"⚠️  LLM initialization warning: {e}")
                logger.warning(f"    System will use context-only fallback for answers")
                self.llm = None
            
            # Initialize Advanced RAG Retriever (hybrid search + caching)
            try:
                if verbose:
                    logger.info(f"🎯 Initializing Advanced RAG (Hybrid + Cache)...")
                
                self.advanced_retriever = AdvancedRAGRetriever(
                    vector_store=self.vector_store,
                    enable_hybrid=True,        # Semantic + keyword search
                    enable_cache=True,         # LRU query caching
                    enable_reranking=False,    # Disabled (adds overhead)
                    hybrid_alpha=0.6,          # 60% semantic, 40% keyword
                    cache_size=200             # Store up to 200 queries
                )
                
                if verbose:
                    logger.info(f"✅ Advanced RAG ready (Hybrid + Cache enabled)")
                    
            except Exception as e:
                logger.warning(f"⚠️  Advanced RAG initialization warning: {e}")
                logger.warning(f"    System will use basic similarity search")
                self.advanced_retriever = None
            
            # Load mapping data
            self.mapping_data = self._load_mapping()
            
            if verbose:
                logger.info(f"✅ Neuronix Query System ready!\n")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    def _load_mapping(self) -> Dict:
        """Load master mapping for metadata"""
        try:
            if MAPPING_FILE.exists():
                with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️  Could not load mapping: {e}")
        
        return {}
    
    def get_db_status(self) -> Dict:
        """Get vector database status"""
        try:
            count = self.vector_store._collection.count()
            
            return {
                "status": "✅ Active",
                "documents_count": count,
                "ready": count > 0,
                "location": str(VECTOR_DB_DIR),
                "model": EMBEDDING_MODEL
            }
        except Exception as e:
            logger.warning(f"⚠️  Database status check error: {e}")
            return {
                "status": "❌ Error",
                "documents_count": 0,
                "ready": False,
                "location": str(VECTOR_DB_DIR),
                "error": str(e)
            }
    
    def retrieve_context(self, query: str, k: Optional[int] = None) -> List[Document]:
        """
        Retrieve top-k most relevant chunks from ChromaDB
        Uses Advanced RAG with hybrid search (semantic + keyword) and query caching
        
        Args:
            query: User question
            k: Number of chunks to retrieve (default: 6, range: 5-8)
            
        Returns:
            List of Document objects with metadata
        """
        if k is None:
            k = QUERY_DEFAULT_K
        
        # Ensure k is within acceptable range
        k = max(RETRIEVAL_K_MIN, min(k, RETRIEVAL_K_MAX))
        
        try:
            if self.verbose:
                logger.info(f"🔍 Query: '{query}'")
                logger.info(f"   Retrieving top {k} chunks...")
            
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
                            if self.verbose:
                                logger.info(f"   💾 Cache HIT ({cache_hit_rate:.1f}%)")
                except Exception:
                    pass  # Stats not available, continue normally
            else:
                # Fallback: Use basic similarity search
                if self.verbose:
                    logger.info(f"   Using basic search (advanced retriever unavailable)")
                results = self.vector_store.similarity_search(query, k=k)
            
            if self.verbose:
                logger.info(f"✅ Found {len(results)} chunks\n")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            # Fallback to basic search
            try:
                return self.vector_store.similarity_search(query, k=k)
            except:
                return []
    
    def is_sufficient_context(self, results: List[Document], threshold: float = 0.3) -> bool:
        """
        Determine if retrieved context is sufficient
        
        Returns:
            True if context is sufficient to generate answer
        """
        if not results:
            return False
        
        # Heuristic: if we retrieved k chunks successfully, context is sufficient
        if len(results) >= RETRIEVAL_K_MIN:
            return True
        
        return False
    
    def format_context_for_llm(self, results: List[Document]) -> str:
        """Format retrieved documents for LLM prompt"""
        if not results:
            return ""
        
        context_parts = []
        
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content
            
            context_parts.append(f"[Source {i}: {source}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def generate_answer(self, query: str, results: List[Document]) -> str:
        """
        Generate answer from retrieved context
        
        Args:
            query: Original user question
            results: Retrieved documents from ChromaDB
            
        Returns:
            Generated answer with citations
        """
        # Check if context is sufficient
        if not self.is_sufficient_context(results):
            if self.verbose:
                logger.warning(f"⚠️  Insufficient context to generate answer")
            
            return INSUFFICIENT_CONTEXT_MSG
        
        # Try LLM-based answer generation
        if self.llm:
            try:
                # Format context
                context_str = self.format_context_for_llm(results)
                
                # Build prompt
                prompt = f"""You are a helpful clinical psychology and medical education assistant.
Answer the user's question based PRIMARILY on the provided textbook excerpts.
Be concise, accurate, and cite your sources clearly.
Use simple, professional Hinglish when appropriate.

QUESTION: {query}

TEXTBOOK CONTEXT:
{context_str}

ANSWER (be concise, cite sources):"""
                
                # Generate response
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
                
                # Extract unique sources
                sources = list(dict.fromkeys([doc.metadata.get('source', 'Unknown') for doc in results]))
                
                # Add citations
                citations = "\n\n📚 Sources:"
                for src in sources:
                    citations += f"\n   • {src}"
                
                return answer + citations
                
            except Exception as e:
                logger.error(f"❌ LLM error: {e}")
                return self._fallback_context_answer(query, results)
        
        else:
            # No LLM available - use context fallback
            return self._fallback_context_answer(query, results)
    
    def _fallback_context_answer(self, query: str, results: List[Document]) -> str:
        """
        Fallback answer when LLM is unavailable
        
        Returns:
            Formatted context with sources
        """
        answer = f"📌 Relevant Information:\n\n"
        
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content[:300]
            
            answer += f"[{i}] {source}\n"
            answer += f"    {content}...\n\n"
        
        return answer
    
    def query(self, question: str, k: Optional[int] = None, generate_answer: bool = True) -> Dict:
        """
        Complete RAG query pipeline
        
        Args:
            question: User question
            k: Number of chunks to retrieve (range: 5-8)
            generate_answer: Whether to generate LLM answer
            
        Returns:
            Dictionary with results, answer, and metadata
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🧠 NEURONIX QUERY")
        logger.info(f"{'='*80}")
        logger.info(f"Question: {question}\n")
        
        if k is None:
            k = QUERY_DEFAULT_K
        
        try:
            # Retrieve context
            results = self.retrieve_context(question, k=k)
            
            if not results:
                logger.warning("❌ No documents found")
                return {
                    "success": False,
                    "query": question,
                    "answer": NO_RESULTS_MSG,
                    "documents": [],
                    "metadata": {
                        "chunks_retrieved": 0,
                        "database_status": self.get_db_status()
                    }
                }
            
            # Generate answer
            answer = ""
            if generate_answer:
                answer = self.generate_answer(question, results)
                if self.verbose:
                    logger.info(f"📝 Answer:\n{answer}\n")
            
            # Format output
            return {
                "success": True,
                "query": question,
                "answer": answer,
                "documents": [
                    {
                        "content": doc.page_content[:500],
                        "source": doc.metadata.get('source', 'Unknown'),
                        "chunk_index": doc.metadata.get('chunk_index', 0),
                        "total_chunks": doc.metadata.get('total_chunks', 0)
                    }
                    for doc in results
                ],
                "metadata": {
                    "chunks_retrieved": len(results),
                    "embedding_model": EMBEDDING_MODEL,
                    "database_status": self.get_db_status(),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            return {
                "success": False,
                "query": question,
                "answer": ERROR_MSG,
                "documents": [],
                "metadata": {
                    "error": str(e),
                    "database_status": self.get_db_status()
                }
            }
    
    def interactive_mode(self):
        """Run interactive query mode"""
        print("\n" + "="*80)
        print("🧠 NEURONIX CLINICAL QUERY SYSTEM")
        print("="*80)
        
        # Check database
        db_status = self.get_db_status()
        print(f"\n📦 Vector Database:")
        print(f"   Status: {db_status['status']}")
        print(f"   Documents: {db_status['documents_count']:,}")
        print(f"   Model: {db_status['model']}\n")
        
        if not db_status['ready']:
            print("❌ Database is empty!")
            print("   Run: python neuronix_ingest.py\n")
            return
        
        print("💡 Ask questions about psychology, clinical concepts, etc.")
        print("   Examples:")
        print("      • What is cognitive behavioral therapy?")
        print("      • How does depression affect the brain?")
        print("      • Types of anxiety disorders")
        print("\n   Type 'quit' to exit\n")
        print("="*80 + "\n")
        
        while True:
            try:
                question = input("❓ Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thank you for using Neuronix!\n")
                    break
                
                if not question:
                    print("Please enter a question.\n")
                    continue
                
                # Process query
                result = self.query(question, k=QUERY_DEFAULT_K, generate_answer=True)
                
                print("\n" + "-"*80)
                print(result['answer'])
                print("-"*80 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")


def main():
    """Main entry point"""
    try:
        # Initialize query system
        query_system = NeuronixQuerySystem(verbose=True)
        
        # Run interactive mode
        query_system.interactive_mode()
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
