"""
Neuronix RAG Query Script
Simple interface to search the vector database for medical/psychology information

Usage:
    python query_rag.py "depression treatment options"
    python query_rag.py "cognitive behavioral therapy"
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Dict

# ================================================================
# WINDOWS COMPATIBILITY FIX
# ================================================================
# Windows doesn't have pwd module (Unix-only)
# langchain_community tries to import it, so we create a mock
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Import RAG Enhancements (reranking, multi-query, compression)
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag_enhancements import EnhancedRAGRetrieval, create_rag_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent
VECTOR_DB_DIR = BASE_DIR / "data" / "vector_db"


class RAGQueryEngine:
    """Simple query interface for the RAG vector database"""
    
    def __init__(self, google_api_key: str = None):
        """Initialize the query engine"""
        # Note: API key no longer needed for embeddings (using HuggingFace)
        
        # Initialize embeddings (HuggingFace - no API key needed)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Load vector store
        self.vector_store = Chroma(
            embedding_function=self.embeddings,
            persist_directory=str(VECTOR_DB_DIR),
            collection_name="neuronix_medical_kb"
        )
        
        # Initialize Enhanced Retriever (reranking, multi-query, compression)
        self.enhanced_retriever = EnhancedRAGRetrieval(
            self.vector_store,
            verbose=False  # Set to True for detailed logs
        )
        
        logger.info(f"[OK] RAG Query Engine initialized")
        logger.info(f"  Database: {VECTOR_DB_DIR}")
        logger.info(f"  Collection: neuronix_medical_kb")
        logger.info(f"  Enhanced Retrieval: ENABLED (reranking, multi-query)")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search the vector database
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of result dictionaries with content and metadata
        """
        logger.info(f"\nSearching for: '{query}'")
        logger.info(f"Retrieving top {k} results...")
        
        try:
            # Perform ENHANCED similarity search (with reranking + multi-query)
            results_raw = self.enhanced_retriever.retrieve_enhanced(
                query=query,
                k=k,
                rerank=True,        # BM25 reranking (25-46% quality improvement)
                compress=False,      # Compression disabled (can enable for token reduction)
                multi_query=True     # Generate query variations (15-30% better recall)
            )
            
            if not results_raw:
                logger.warning("No results found")
                return []
            
            # Format results (enhanced retrieval returns dict objects)
            formatted_results = []
            for i, result in enumerate(results_raw, 1):
                formatted_result = {
                    'rank': i,
                    'content': result['content'],
                    'metadata': result.get('metadata', {}),
                    'source': result.get('source', 'Unknown'),
                    'country': result.get('metadata', {}).get('country', 'Unknown'),
                    'status': result.get('metadata', {}).get('status_label', 'Unknown'),
                    'chunk': f"{result.get('metadata', {}).get('chunk_index', '?')}/{result.get('metadata', {}).get('total_chunks', '?')}",
                    'relevance_score': result.get('similarity_score', 0)
                }
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def print_results(self, results: List[Dict], query: str = ""):
        """Print formatted search results"""
        if not results:
            print("\n[!] No results found\n")
            return
        
        print("\n" + "=" * 100)
        print(f"SEARCH RESULTS for '{query}'")
        print("=" * 100 + "\n")
        
        for result in results:
            print(f"Result #{result['rank']}")
            print("─" * 100)
            print(f"Source:  {result['source']}")
            print(f"Country: {result['country']}")
            print(f"Status:  {result['status']}")
            print(f"Chunk:   {result['chunk']}")
            print(f"\nContent:")
            print(f"{result['content'][:800]}...")
            print("\n")
        
        print("=" * 100)
        print(f"Displayed {len(results)} result(s)")
        print("=" * 100 + "\n")


def interactive_search():
    """Run interactive search mode"""
    import sys
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("[ERROR] Error: GOOGLE_API_KEY environment variable not set")
        print("Set it with: $env:GOOGLE_API_KEY = 'your-key'")
        sys.exit(1)
    
    try:
        engine = RAGQueryEngine(google_api_key=google_api_key)
    except Exception as e:
        print(f"[ERROR] Failed to initialize query engine: {e}")
        print(f"Make sure you've run: python scripts/ingest_data.py")
        sys.exit(1)
    
    print("\n" + "=" * 100)
    print("NEURONIX RAG QUERY ENGINE - Interactive Mode")
    print("=" * 100)
    print("Enter search queries about medical/psychology topics")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            query = input("Query> ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Exiting...\n")
                break
            
            if not query:
                print("Please enter a query\n")
                continue
            
            results = engine.search(query, k=5)
            engine = RAGQueryEngine(google_api_key=google_api_key)  # Reinitialize for fresh search
            results = engine.search(query, k=5)
            
            # Print results
            if results:
                print(f"\n{'─' * 100}")
                for result in results:
                    print(f"\nResult #{result['rank']} - {result['source']} ({result['country']})")
                    print(f"Status: {result['status']} | Chunk: {result['chunk']}")
                    print(f"\n{result['content'][:600]}...\n")
                print(f"{'─' * 100}\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting...\n")
            break
        except Exception as e:
            print(f"Error: {e}\n")


def main():
    """Main entry point"""
    
    # Check for Google API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("\n" + "!" * 100)
        print("ERROR: GOOGLE_API_KEY environment variable not set")
        print("!" * 100)
        print("\nSet your API key:")
        print("  Windows (PowerShell): $env:GOOGLE_API_KEY = 'your-api-key'")
        print("  Windows (CMD): set GOOGLE_API_KEY=your-api-key")
        print("  Linux/Mac: export GOOGLE_API_KEY='your-api-key'")
        print("\nGet your key from: https://makersuite.google.com/app/apikey")
        print("!" * 100 + "\n")
        sys.exit(1)
    
    # Check if vector database exists
    if not VECTOR_DB_DIR.exists():
        print("\n" + "!" * 100)
        print("ERROR: Vector database not found at:", VECTOR_DB_DIR)
        print("!" * 100)
        print("\nRun the ingestion pipeline first:")
        print("  python scripts/ingest_data.py")
        print("!" * 100 + "\n")
        sys.exit(1)
    
    try:
        # Get query from command line or run interactive mode
        if len(sys.argv) > 1:
            # Command line query
            query = " ".join(sys.argv[1:])
            
            engine = RAGQueryEngine(google_api_key=google_api_key)
            results = engine.search(query, k=5)
            
            # Print formatted results
            engine.print_results(results, query)
            
        else:
            # Interactive mode
            interactive_search()
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check GOOGLE_API_KEY is set correctly")
        print("2. Ensure vector database was created: python scripts/ingest_data.py")
        print("3. Check /data/vector_db directory exists")
        sys.exit(1)


if __name__ == "__main__":
    main()
