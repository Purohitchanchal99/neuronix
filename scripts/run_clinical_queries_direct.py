#!/usr/bin/env python3
"""
Direct Clinical Query Execution
Queries the existing vector database without re-ingestion
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import logging

# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(message)s'
)

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    try:
        # Direct ChromaDB import and access
        import chromadb
        from chromadb.config import Settings
        
        # Initialize ChromaDB client with existing database
        db_path = Path("data/vector_db")
        
        if not db_path.exists():
            print(f"❌ Database not found at: {db_path}")
            return
        
        # Connect to existing ChromaDB
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_collection(name="psychology_docs")
        
        # Get collection stats
        count = collection.count()
        print(f"\n{'='*80}")
        print(f"CLINICAL QUERIES - RAG System")
        print(f"{'='*80}")
        print(f"📊 Database Status: {count} documents indexed\n")
        
        if count == 0:
            print("❌ Database is empty. Documents not yet ingested.")
            return
        
        # Initialize Google Generative AI for embeddings and LLM
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("⚠️  Note: GOOGLE_API_KEY not set. Queries may fail.")
                print("   Set environment variable to enable LLM answers.\n")
            else:
                genai.configure(api_key=api_key)
            
            embedding_model = genai.embedding_models[0] if genai.embedding_models else None
            llm_model = genai.GenerativeModel("gemini-pro")
        except Exception as e:
            print(f"⚠️  Could not initialize Google AI: {str(e)[:100]}")
            embedding_model = None
            llm_model = None
        
        # Clinical queries
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
        
        for i, query in enumerate(queries, 1):
            print(f"\n{'─'*80}")
            print(f"Query {i}: {query}")
            print(f"{'─'*80}")
            
            try:
                # Query the database
                results_raw = collection.query(
                    query_texts=[query],
                    n_results=5,
                    include=["documents", "metadatas", "distances"]
                )
                
                if not results_raw["documents"] or not results_raw["documents"][0]:
                    print("❌ No results found in database")
                    continue
                
                # Display retrieved documents
                print(f"\n📚 Retrieved Documents:\n")
                retrieved_docs = []
                for j, (doc, meta, dist) in enumerate(
                    zip(
                        results_raw["documents"][0],
                        results_raw["metadatas"][0],
                        results_raw["distances"][0]
                    ),
                    1
                ):
                    # Convert distance to similarity score (lower distance = higher similarity)
                    similarity = 1 - (dist / 2)  # Normalize to 0-1
                    similarity = max(0, min(1, similarity))  # Clamp between 0-1
                    
                    source = meta.get("source", "Unknown") if isinstance(meta, dict) else "Unknown"
                    
                    # Determine relevance tier
                    if similarity > 0.85:
                        tier = "⭐⭐⭐⭐⭐ Excellent"
                    elif similarity > 0.75:
                        tier = "⭐⭐⭐⭐ Very Good"
                    elif similarity > 0.60:
                        tier = "⭐⭐⭐ Good"
                    elif similarity > 0.45:
                        tier = "⭐⭐ Fair"
                    else:
                        tier = "⭐ Poor"
                    
                    preview = doc[:100].replace('\n', ' ') if doc else "No content"
                    
                    print(f"  [{j}] Similarity: {similarity:.3f} {tier}")
                    print(f"      Source: {source}")
                    print(f"      Preview: {preview}...")
                    
                    retrieved_docs.append({
                        "rank": j,
                        "similarity": round(similarity, 3),
                        "source": source,
                        "content": doc[:500]
                    })
                
                # Generate answer using LLM if available
                print(f"\n💭 Generating Answer...\n")
                
                if llm_model and retrieved_docs:
                    try:
                        context = "\n\n".join([
                            f"[Source {i}: {doc['source']}]\n{doc['content'][:300]}"
                            for i, doc in enumerate(retrieved_docs[:2], 1)
                        ])
                        
                        prompt = f"""Based on the following psychology textbook excerpts, provide a comprehensive clinical answer to the question.

Question: {query}

Context from textbooks:
{context}

Answer based on the textbooks:"""
                        
                        response = llm_model.generate_content(
                            prompt,
                            generation_config={
                                "temperature": 0.7,
                                "max_output_tokens": 500
                            }
                        )
                        
                        answer = response.text if response.text else "No answer generated"
                        print(f"📄 Answer:\n{answer}\n")
                        
                    except Exception as e:
                        print(f"⚠️  Could not generate LLM answer: {str(e)[:100]}")
                        print(f"   Retrieved top documents are shown above.\n")
                else:
                    print("⚠️  LLM not available for answer generation")
                    print("   Retrieved documents shown above.\n")
                
                # Store result
                results.append({
                    "query_num": i,
                    "query": query,
                    "retrieved_count": len(retrieved_docs),
                    "retrieved_docs": retrieved_docs,
                    "status": "Success"
                })
                
            except Exception as e:
                print(f"❌ Error processing query: {str(e)}\n")
                results.append({
                    "query_num": i,
                    "query": query,
                    "error": str(e),
                    "status": "Error"
                })
        
        # Summary
        print(f"\n{'='*80}")
        print("📊 SUMMARY")
        print(f"{'='*80}")
        successful = sum(1 for r in results if r["status"] == "Success")
        print(f"✅ Successful: {successful}/{len(queries)}")
        print(f"⏱️  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📦 Database: {count} documents\n")
        
        # Save results to JSON
        output_file = Path("clinical_queries_output.json")
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "database_count": count,
                "queries_executed": len(queries),
                "successful": successful,
                "results": results
            }, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Install required packages: pip install chromadb google-generativeai")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
