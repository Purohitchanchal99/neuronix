"""
Smart RAG Evaluation - Works with in-progress ingestion
========================================================
Evaluates RAG system with 20 queries, handles database growth
"""

import sys
import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Windows compatibility
if sys.platform == "win32":
    import types
    pwd_module = types.ModuleType('pwd')
    sys.modules['pwd'] = pwd_module

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

class SmartRAGEvaluator:
    """Evaluate RAG with adaptive retry logic"""
    
    def __init__(self):
        """Initialize with retry logic"""
        logger.info("🔧 Initializing Smart RAG Evaluator...")
        
        # Load dependencies
        from langchain_chroma import Chroma
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.vector_store = Chroma(
            collection_name="neuronix_medical_kb",
            persist_directory=str(VECTOR_DB_DIR),
            embedding_function=self.embeddings
        )
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        logger.info("✅ Evaluator initialized\n")
    
    def get_db_stats(self) -> Dict:
        """Get database statistics"""
        try:
            count = self.vector_store._collection.count()
            return {
                "status": "active",
                "document_count": count,
                "ready": count > 0
            }
        except Exception as e:
            return {"status": "error", "document_count": 0, "ready": False, "error": str(e)}
    
    def retrieve_with_scores(self, query: str, k: int = 5, retry: int = 3) -> List[Dict]:
        """Retrieve with retry logic"""
        for attempt in range(retry):
            try:
                results = self.vector_store.similarity_search_with_score(query, k=k)
                return [
                    {
                        "document": doc,
                        "similarity_score": float(score),
                        "content_preview": doc.page_content[:120] + "..." if len(doc.page_content) > 120 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc, score in results
                ]
            except Exception as e:
                if attempt < retry - 1:
                    logger.warning(f"Retry {attempt + 1}/{retry}: {str(e)[:50]}...")
                    time.sleep(2)
                else:
                    logger.error(f"Failed after {retry} attempts: {e}")
                    return []
        return []
    
    def generate_answer(self, query: str, chunks: List[Dict]) -> Tuple[str, float]:
        """Generate answer with error handling"""
        if not chunks:
            return "No relevant documents found in database.", 0.0
        
        context = "\n\n".join([
            f"Source: {c['metadata'].get('source', 'Unknown')}\n{c['document'].page_content[:300]}"
            for c in chunks[:3]
        ])
        
        prompt = f"""Psychology Question: {query}

Based on textbook excerpts (if available):
{context}

Provide a concise educational answer citing sources when possible:"""
        
        try:
            start = time.time()
            response = self.llm.invoke(prompt)
            elapsed = time.time() - start
            ans = response.content if hasattr(response, 'content') else str(response)
            return ans[:800], elapsed  # Limit to 800 chars for this summary
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"Error: Could not generate answer", 0.0
    
    def evaluate_one_query(self, query: str, query_num: int) -> Dict:
        """Evaluate single query and return metrics"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Query {query_num}: {query}")
        logger.info('='*70)
        
        start_time = time.time()
        
        # Retrieve
        retrieved = self.retrieve_with_scores(query, k=5)
        retrieval_time = time.time() - start_time
        
        # Generate answer
        answer, gen_time = self.generate_answer(query, retrieved)
        total_time = time.time() - start_time
        
        # Calculate metrics
        if retrieved:
            scores = [r["similarity_score"] for r in retrieved]
            excellent = sum(1 for s in scores if s < 0.3)
            avg_score = sum(scores) / len(scores)
            relevant_pct = ((excellent + sum(1 for s in scores if s < 0.7)) / len(scores)) * 100
        else:
            avg_score = 999
            relevant_pct = 0
            excellent = 0
        
        # Display
        logger.info(f"⏱️  Total Time: {total_time:.2f}s")
        logger.info(f"📊 Retrieval Accuracy: {relevant_pct:.1f}%")
        logger.info(f"🎯 Avg Similarity: {avg_score:.3f}")
        logger.info(f"📚 Documents Found: {len(retrieved)}")
        
        if retrieved:
            logger.info(f"\n📖 Retrieved Chunks:")
            for i, chunk in enumerate(retrieved, 1):
                logger.info(f"  [{i}] Score: {chunk['similarity_score']:.3f} | {chunk['metadata'].get('source', 'Unknown')}")
                logger.info(f"      {chunk['content_preview'][:100]}...")
        
        logger.info(f"\n💡 Answer: {answer[:200]}...\n")
        
        return {
            "query": query,
            "query_num": query_num,
            "retrieved_count": len(retrieved),
            "avg_similarity": avg_score,
            "relevant_percent": relevant_pct,
            "retrieval_time": retrieval_time,
            "generation_time": gen_time,
            "total_time": total_time,
            "answer_preview": answer[:150],
            "chunks": [
                {
                    "similarity": r["similarity_score"],
                    "source": r["metadata"].get("source", "Unknown"),
                    "preview": r["content_preview"][:100]
                }
                for r in retrieved
            ]
        }
    
    def run_20_query_evaluation(self) -> Dict:
        """Run 20 test queries"""
        
        # Check DB status first
        db_stats = self.get_db_stats()
        logger.info(f"📊 Database Status: {db_stats['document_count']} documents")
        logger.info(f"{'='*70}\n")
        
        test_queries = [
            "What is cognitive psychology?",
            "Define classical conditioning and give examples",
            "Explain the difference between nature and nurture",
            "What are the diagnostic criteria for depression?",
            "How is cognitive behavioral therapy used in treatment?",
            "What is PTSD?",
            "Describe Erikson's stages of development",
            "What is attachment theory?",
            "How do cognitive abilities change during adolescence?",
            "Explain the function of the prefrontal cortex",
            "What role do neurotransmitters play?",
            "How does neuroplasticity contribute to learning?",
            "What are the types of sensory receptors?",
            "Explain sensation vs perception",
            "How does the brain process color?",
            "What are types of memory in Atkinson-Shiffrin model?",
            "Explain encoding, storage, and retrieval",
            "What is metacognition?",
            "Describe Maslow's hierarchy of needs",
            "What are the theories of emotion?"
        ]
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "db_status": db_stats,
            "total_queries": len(test_queries),
            "queries": []
        }
        
        all_times = []
        all_relevant = []
        all_similarities = []
        
        try:
            for idx, query in enumerate(test_queries, 1):
                try:
                    query_result = self.evaluate_one_query(query, idx)
                    results["queries"].append(query_result)
                    
                    all_times.append(query_result["total_time"])
                    all_relevant.append(query_result["relevant_percent"])
                    if query_result["avg_similarity"] < 100:
                        all_similarities.append(query_result["avg_similarity"])
                    
                except Exception as e:
                    logger.error(f"Query {idx} failed: {e}")
                    results["queries"].append({
                        "query": query,
                        "query_num": idx,
                        "error": str(e)
                    })
                    continue
        
        except KeyboardInterrupt:
            logger.info("\n⚠️ Evaluation interrupted by user")
        
        # Aggregate metrics
        if all_times:
            results["metrics"] = {
                "avg_response_time": sum(all_times) / len(all_times),
                "min_response_time": min(all_times),
                "max_response_time": max(all_times),
                "total_evaluation_time": sum(all_times),
                "avg_retrieval_accuracy": sum(all_relevant) / len(all_relevant) if all_relevant else 0,
                "avg_similarity_score": sum(all_similarities) / len(all_similarities) if all_similarities else 0,
                "successful_queries": len([q for q in results["queries"] if "error" not in q]),
                "failed_queries": len([q for q in results["queries"] if "error" in q])
            }
        
        return results
    
    def save_results(self, results: Dict):
        """Save results to JSON and markdown"""
        
        # JSON
        json_file = BASE_DIR / "rag_evaluation_results.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"\n✅ JSON saved: {json_file}")
        
        # Markdown summary
        md_file = BASE_DIR / "RAG_EVALUATION_RESULTS.md"
        md_content = f"""# RAG System Evaluation Results

**Date:** {results['timestamp']}  
**Database Status:** {results['db_status']['document_count']} documents

## Summary Metrics

"""
        if "metrics" in results:
            m = results["metrics"]
            md_content += f"""
| Metric | Value |
|--------|-------|
| Queries Tested | {m['successful_queries']}/{results['total_queries']} |
| Avg Response Time | {m['avg_response_time']:.2f}s |
| Min/Max Time | {m['min_response_time']:.2f}s / {m['max_response_time']:.2f}s |
| Avg Retrieval Accuracy | {m['avg_retrieval_accuracy']:.1f}% |
| Avg Similarity Score | {m['avg_similarity_score']:.3f} |

## Query-by-Query Results

"""
            for q in results["queries"]:
                if "error" not in q:
                    md_content += f"""### Q{q['query_num']}: {q['query']}
- Response Time: {q['total_time']:.2f}s
- Retrieved: {q['retrieved_count']} documents
- Accuracy: {q['relevant_percent']:.1f}%
- Answer: {q['answer_preview']}...

"""
        
        with open(md_file, 'w') as f:
            f.write(md_content)
        logger.info(f"✅ Markdown saved: {md_file}\n")


def main():
    try:
        evaluator = SmartRAGEvaluator()
        
        logger.info("🚀 Starting 20-Query Evaluation\n")
        results = evaluator.run_20_query_evaluation()
        
        # Save results
        evaluator.save_results(results)
        
        # Print summary
        if "metrics" in results:
            m = results["metrics"]
            print("\n" + "="*70)
            print("✅ EVALUATION COMPLETE")
            print("="*70)
            print(f"\n📊 Results Summary:")
            print(f"   Successful Queries: {m['successful_queries']}/{results['total_queries']}")
            print(f"   Avg Response Time: {m['avg_response_time']:.2f}s")
            print(f"   Retrieval Accuracy: {m['avg_retrieval_accuracy']:.1f}%")
            print(f"   Avg Similarity: {m['avg_similarity_score']:.3f}")
            print(f"   Total Time: {m['total_evaluation_time']:.1f}s")
            print("\n" + "="*70)
        
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
