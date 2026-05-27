"""
Run specific clinical queries and display detailed results
"""

import sys
import os
import time
from pathlib import Path

# Windows compatibility
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

def run_clinical_queries():
    """Run 7 clinical queries and display results"""
    
    try:
        from langchain_chroma import Chroma
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        print("\n" + "="*80)
        print("🏥 CLINICAL QUERIES - RAG SYSTEM")
        print("="*80)
        
        # Initialize
        print("\n🔧 Initializing system...")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = Chroma(
            collection_name="neuronix_medical_kb",
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=embeddings
        )
        llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        
        db_count = vector_store._collection.count()
        print(f"✅ Database ready: {db_count} documents\n")
        
        # Queries to run
        queries = [
            "What is schizophrenia?",
            "Symptoms of major depressive disorder",
            "Treatment for anxiety disorders",
            "DSM-5 criteria for ADHD",
            "What is bipolar disorder?",
            "PTSD diagnosis criteria",
            "Difference between neurosis and psychosis"
        ]
        
        results = []
        
        for idx, query in enumerate(queries, 1):
            print(f"\n{'='*80}")
            print(f"Query {idx}/7: {query}")
            print('='*80)
            
            start_time = time.time()
            
            # Retrieve documents
            retrieved = vector_store.similarity_search_with_score(query, k=5)
            retrieval_time = time.time() - start_time
            
            print(f"\n📖 Retrieved Chunks (Retrieval Time: {retrieval_time:.2f}s):\n")
            
            chunks_data = []
            for chunk_idx, (doc, score) in enumerate(retrieved, 1):
                relevance = "⭐⭐⭐⭐⭐ Excellent" if score < 0.3 else \
                           "⭐⭐⭐⭐ Very Good" if score < 0.5 else \
                           "⭐⭐⭐ Good" if score < 0.7 else \
                           "⭐⭐ Fair" if score < 0.9 else "⭐ Poor"
                
                print(f"[{chunk_idx}] Similarity: {score:.3f} | {relevance}")
                print(f"    Source: {doc.metadata.get('source', 'Unknown')}")
                print(f"    Content: {doc.page_content[:100]}...")
                print()
                
                chunks_data.append({
                    "index": chunk_idx,
                    "similarity": float(score),
                    "relevance": relevance,
                    "source": doc.metadata.get("source", "Unknown"),
                    "preview": doc.page_content[:100]
                })
            
            # Generate answer
            print("\n💡 Generating Answer...\n")
            
            context = "\n\n".join([
                f"[{doc.metadata.get('source', 'Unknown')}]\n{doc.page_content[:250]}"
                for doc, _ in retrieved[:3]
            ])
            
            prompt = f"""As a clinical psychology educator, answer this question based on the provided textbook excerpts:

Question: {query}

Textbook Context:
{context}

Provide a clear, accurate answer with relevant clinical details. Include citations when available."""
            
            gen_start = time.time()
            response = llm.invoke(prompt)
            gen_time = time.time() - gen_start
            
            answer = response.content if hasattr(response, 'content') else str(response)
            
            total_time = time.time() - start_time
            
            print(f"📝 Answer (Generation Time: {gen_time:.2f}s):\n")
            print(answer)
            
            print(f"\n⏱️  Total Time: {total_time:.2f}s")
            
            results.append({
                "query_num": idx,
                "query": query,
                "chunks": chunks_data,
                "answer": answer,
                "retrieval_time": retrieval_time,
                "generation_time": gen_time,
                "total_time": total_time
            })
        
        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        
        total_response_time = sum(r["total_time"] for r in results)
        avg_response_time = total_response_time / len(results)
        
        print(f"\nQueries Executed: {len(results)}/7 ✅")
        print(f"Total Time: {total_response_time:.2f}s")
        print(f"Average Time per Query: {avg_response_time:.2f}s")
        print(f"Success Rate: 100%\n")
        
        # Query summary table
        print("\nQuery Summary:")
        print("-" * 80)
        print(f"{'Q#':<3} {'Query':<40} {'Time':<8} {'Status'}")
        print("-" * 80)
        
        for r in results:
            print(f"{r['query_num']:<3} {r['query'][:40]:<40} {r['total_time']:.2f}s  ✅")
        
        print("-" * 80)
        
        return results
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    results = run_clinical_queries()
    
    if results:
        print("\n" + "="*80)
        print("✅ ALL QUERIES COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
