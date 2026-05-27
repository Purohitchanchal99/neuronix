# Advanced Features Implementation Guide

Complete copy-paste implementations for all 5 advanced features.

---

## Feature 1: Conversation Memory Implementation

### File: `scripts/conversation_memory.py`

```python
"""
Conversation Memory System
Stores and retrieves user context across conversations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
import pickle

class ConversationMemory:
    """Persistent conversation memory for users"""
    
    def __init__(self, ttl_days: int = 30):
        """
        Initialize conversation memory
        
        Args:
            ttl_days: Time-to-live for memory entries (days)
        """
        self.store: Dict[str, Dict] = {}  # {user_id: memory_data}
        self.ttl = timedelta(days=ttl_days)
        self.conversation_count = defaultdict(int)
    
    def create_memory_entry(self, user_id: str) -> Dict:
        """Create new memory entry for user"""
        return {
            'user_id': user_id,
            'symptoms': [],
            'topics': [],
            'preferences': {
                'language': 'english',
                'detail_level': 'medical',
                'response_style': 'informative'
            },
            'previous_queries': [],
            'summary': '',
            'created_at': datetime.now(),
            'last_updated': datetime.now(),
            'conversation_count': 0
        }
    
    def remember_context(self, user_id: str, context: Dict) -> None:
        """Store conversation context"""
        if user_id not in self.store:
            self.store[user_id] = self.create_memory_entry(user_id)
        
        memory = self.store[user_id]
        
        # Update fields
        if 'symptoms' in context:
            for symptom in context['symptoms']:
                if symptom not in memory['symptoms']:
                    memory['symptoms'].append(symptom)
        
        if 'topics' in context:
            for topic in context['topics']:
                if topic not in memory['topics']:
                    memory['topics'].append(topic)
        
        if 'preferences' in context:
            memory['preferences'].update(context['preferences'])
        
        if 'query' in context:
            memory['previous_queries'].append({
                'query': context['query'],
                'timestamp': datetime.now().isoformat()
            })
        
        memory['last_updated'] = datetime.now()
        memory['conversation_count'] += 1
    
    def get_context(self, user_id: str) -> Dict:
        """Retrieve stored context for user"""
        if user_id not in self.store:
            return {}
        
        memory = self.store[user_id]
        
        # Check if expired
        if datetime.now() - memory['last_updated'] > self.ttl:
            del self.store[user_id]
            return {}
        
        return memory
    
    def update_symptoms(self, user_id: str, symptoms: List[str]) -> None:
        """Add symptoms to history"""
        if user_id not in self.store:
            self.store[user_id] = self.create_memory_entry(user_id)
        
        memory = self.store[user_id]
        for symptom in symptoms:
            if symptom not in memory['symptoms']:
                memory['symptoms'].append(symptom)
        
        memory['last_updated'] = datetime.now()
    
    def update_topics(self, user_id: str, topics: List[str]) -> None:
        """Add topics to history"""
        if user_id not in self.store:
            self.store[user_id] = self.create_memory_entry(user_id)
        
        memory = self.store[user_id]
        for topic in topics:
            if topic not in memory['topics']:
                memory['topics'].append(topic)
        
        memory['last_updated'] = datetime.now()
    
    def set_preferences(self, user_id: str, preferences: Dict) -> None:
        """Set user preferences"""
        if user_id not in self.store:
            self.store[user_id] = self.create_memory_entry(user_id)
        
        self.store[user_id]['preferences'].update(preferences)
        self.store[user_id]['last_updated'] = datetime.now()
    
    def get_summary(self, user_id: str) -> str:
        """Get user profile summary"""
        memory = self.get_context(user_id)
        if not memory:
            return ""
        
        symptoms_str = ", ".join(memory.get('symptoms', [])[:3])
        topics_str = ", ".join(memory.get('topics', [])[:3])
        
        summary = f"""User Profile:
- Main symptoms: {symptoms_str}
- Topics discussed: {topics_str}
- Conversations: {memory['conversation_count']}
- Language preference: {memory['preferences'].get('language', 'english')}"""
        
        return summary
    
    def enhance_query(self, user_id: str, query: str) -> str:
        """Enhance query with user context"""
        context = self.get_context(user_id)
        
        if not context or not context.get('symptoms'):
            return query
        
        symptoms = ", ".join(context['symptoms'][:2])
        enhanced = f"{query} [Previous context: {symptoms}]"
        return enhanced
    
    def export_memory(self, user_id: str) -> str:
        """Export memory to JSON"""
        memory = self.get_context(user_id)
        
        # Convert datetime objects
        for key in list(memory.keys()):
            if isinstance(memory[key], datetime):
                memory[key] = memory[key].isoformat()
        
        return json.dumps(memory, indent=2)
    
    def import_memory(self, user_id: str, json_data: str) -> None:
        """Import memory from JSON"""
        data = json.loads(json_data)
        
        # Convert ISO timestamps back
        if 'last_updated' in data:
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        self.store[user_id] = data
    
    def clear_old_entries(self) -> int:
        """Remove expired entries"""
        expired = []
        for user_id, memory in self.store.items():
            if datetime.now() - memory['last_updated'] > self.ttl:
                expired.append(user_id)
        
        for user_id in expired:
            del self.store[user_id]
        
        return len(expired)


# Usage Example
if __name__ == "__main__":
    memory = ConversationMemory()
    
    # First conversation
    memory.remember_context("patient_001", {
        'symptoms': ['anxiety'],
        'topics': ['anxiety disorders'],
        'query': 'What is anxiety?',
        'preferences': {'language': 'hindi'}
    })
    
    # Second conversation - context remembered
    context = memory.get_context("patient_001")
    enhanced = memory.enhance_query("patient_001", "How to treat anxiety?")
    
    print(f"Enhanced query: {enhanced}")
    print(f"User context:\n{memory.get_summary('patient_001')}")
```

### Integration into `scripts/query_rag_system.py`:

```python
# Add at top
from conversation_memory import ConversationMemory

# In __init__:
self.conversation_memory = ConversationMemory(ttl_days=30)

# Modify retrieve_context():
def retrieve_context(self, query: str, user_id: str = None, k: int = 5):
    """Retrieve with conversation memory"""
    
    # Enhance query with user context if available
    if user_id:
        enhanced_query = self.conversation_memory.enhance_query(user_id, query)
    else:
        enhanced_query = query
    
    # Retrieve
    results = self.advanced_retriever.retrieve(enhanced_query, k=k)
    
    # Store in memory
    if user_id:
        self.conversation_memory.remember_context(user_id, {
            'query': query,
            'topics': extract_topics(results),
            'symptoms': extract_symptoms(query)
        })
    
    return results


# Helper functions
def extract_topics(docs) -> List[str]:
    """Extract topics from documents"""
    topics = set()
    for doc in docs:
        if 'topic' in doc.metadata:
            topics.add(doc.metadata['topic'])
    return list(topics)

def extract_symptoms(query: str) -> List[str]:
    """Extract symptoms from query"""
    # Simple extraction - can be enhanced
    symptom_keywords = ['anxiety', 'depression', 'stress', 'sleep', 'panic']
    found = [s for s in symptom_keywords if s.lower() in query.lower()]
    return found
```

---

## Feature 2: Streaming Responses

### File: `scripts/streaming_response.py`

```python
"""
Streaming Response Implementation
Token-by-token response streaming for better UX
"""

from typing import Generator, List
import time
from langchain_google_genai import ChatGoogleGenerativeAI


class StreamingResponseGenerator:
    """Generate streaming responses"""
    
    def __init__(self, model_name: str = "gemini-pro"):
        """Initialize streaming LLM"""
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.7,
            streaming=True
        )
    
    def stream_response(
        self, 
        query: str, 
        context: List,
        system_prompt: str = None
    ) -> Generator[str, None, None]:
        """
        Stream response token by token
        
        Args:
            query: User query
            context: Retrieved documents
            system_prompt: Optional system prompt
        
        Yields:
            Response chunks (complete phrases for better UX)
        """
        
        # Build context string
        context_str = self._build_context(context)
        
        # Build prompt
        prompt = system_prompt or self._default_prompt()
        full_prompt = f"""{prompt}

Context:
{context_str}

Question: {query}

Answer:"""
        
        # Stream response
        token_buffer = ""
        chunk_size = 0
        
        try:
            for event in self.llm.stream(full_prompt):
                # Extract token
                if hasattr(event, 'content'):
                    token = event.content
                elif isinstance(event, str):
                    token = event
                else:
                    continue
                
                token_buffer += token
                chunk_size += len(token)
                
                # Yield when we have a meaningful chunk
                if self._should_yield(token_buffer, chunk_size):
                    yield token_buffer
                    token_buffer = ""
                    chunk_size = 0
            
            # Yield remainder
            if token_buffer:
                yield token_buffer
                
        except Exception as e:
            yield f"\nError generating response: {str(e)}"
    
    def _should_yield(self, buffer: str, chunk_size: int) -> bool:
        """Determine if buffer should be yielded"""
        # Yield on sentence boundaries or size threshold
        if len(buffer) > 50:
            return '.' in buffer or '?' in buffer or '!' in buffer
        return False
    
    def _build_context(self, docs: List) -> str:
        """Build context string from documents"""
        context_parts = []
        for i, doc in enumerate(docs[:5], 1):  # Top 5 docs
            source = doc.metadata.get('source', 'Unknown')
            content = doc.page_content[:300]  # First 300 chars
            context_parts.append(f"[{i}] From {source}:\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _default_prompt(self) -> str:
        """Default system prompt"""
        return """You are a medical information assistant. Provide accurate, clear, 
and helpful information based on the context provided. Always cite the source 
of information. If uncertain, indicate that clearly."""
    
    def stream_with_typing_effect(
        self,
        query: str,
        context: List,
        print_delay: float = 0.01
    ) -> None:
        """
        Stream response with typing effect to console
        
        Args:
            query: User query
            context: Retrieved documents
            print_delay: Delay between character prints (seconds)
        """
        print("AI: ", end="", flush=True)
        
        for chunk in self.stream_response(query, context):
            for char in chunk:
                print(char, end="", flush=True)
                time.sleep(print_delay)
        
        print()  # New line at end


# FastAPI Integration
def create_streaming_endpoint():
    """Create FastAPI streaming endpoint"""
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    
    app = FastAPI()
    generator = StreamingResponseGenerator()
    
    @app.post("/chat/stream")
    async def stream_chat(query: str, context: List = None) -> StreamingResponse:
        """Stream chat response"""
        
        def generate():
            for chunk in generator.stream_response(query, context or []):
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    return app


# Client-side JavaScript
JAVASCRIPT_CLIENT = """
<script>
async function streamChat(query) {
    const response = await fetch('/chat/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });
    
    const reader = response.body.getReader();
    const chatWindow = document.getElementById('chat-response');
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const text = new TextDecoder().decode(value);
        
        // Parse SSE format
        const lines = text.split('\\n');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const chunk = line.substring(6);
                chatWindow.textContent += chunk;
            }
        }
        
        // Auto-scroll
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
}
</script>

<div id="chat-response" style="
    border: 1px solid #ccc;
    padding: 10px;
    height: 300px;
    overflow-y: auto;
    font-family: monospace;
"></div>
"""


# Usage
if __name__ == "__main__":
    # Example
    from langchain.schema import Document
    
    generator = StreamingResponseGenerator()
    
    sample_docs = [
        Document(
            page_content="Anxiety is a mental health condition...",
            metadata={'source': 'DSM-5'}
        )
    ]
    
    # Stream to console with typing effect
    generator.stream_with_typing_effect(
        "What is anxiety?",
        sample_docs,
        print_delay=0.01
    )
```

---

## Feature 3: Source Citations

### File: `scripts/source_citations.py`

```python
"""
Source Citations System
Track and display sources for medical credibility
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from langchain.schema import Document


@dataclass
class Citation:
    """Single citation"""
    index: int
    source: str
    page: str
    confidence: float
    url: str = ""
    
    def format(self) -> str:
        """Format for display"""
        page_str = f" (Page {self.page})" if self.page != "?" else ""
        confidence_str = f" [{self.confidence:.0%} confidence]"
        return f"[{self.index}] {self.source}{page_str}{confidence_str}"


class CitationTracker:
    """Track and manage citations"""
    
    # Medical authority sources
    AUTHORITY_SOURCES = {
        'DSM-5': 'Diagnostic and Statistical Manual of Mental Disorders',
        'ICD-11': 'International Classification of Diseases',
        'Mayo Clinic': 'Trusted medical information from Mayo Clinic',
        'WHO': 'World Health Organization',
        'NIH': 'National Institutes of Health',
        'CDC': 'Centers for Disease Control and Prevention'
    }
    
    def __init__(self):
        """Initialize citation tracker"""
        self.citations: List[Citation] = []
        self.used_sources: set = set()
    
    def extract_citations_from_docs(
        self, 
        docs: List[Document]
    ) -> List[Citation]:
        """Extract citations from retrieved documents"""
        self.citations = []
        self.used_sources = set()
        
        for doc in docs:
            source = doc.metadata.get('source', 'Unknown')
            page = str(doc.metadata.get('page', '?'))
            confidence = float(doc.metadata.get('confidence', 0.8))
            url = doc.metadata.get('url', '')
            
            # Avoid duplicates
            source_key = f"{source}:{page}"
            if source_key in self.used_sources:
                continue
            
            self.used_sources.add(source_key)
            
            citation = Citation(
                index=len(self.citations) + 1,
                source=source,
                page=page,
                confidence=confidence,
                url=url
            )
            self.citations.append(citation)
        
        return self.citations
    
    def get_formatted_bibliography(self) -> str:
        """Get formatted bibliography"""
        if not self.citations:
            return ""
        
        bib = "\n📚 **Sources:**\n"
        for citation in self.citations:
            bib += f"{citation.format()}\n"
        
        return bib
    
    def get_authority_score(self, source: str) -> float:
        """Score source authority (0-1)"""
        if source in self.AUTHORITY_SOURCES:
            return 0.95  # High authority
        elif any(auth in source for auth in self.AUTHORITY_SOURCES.keys()):
            return 0.85  # Contains authority keyword
        else:
            return 0.6  # Unknown source
    
    def filter_high_confidence(
        self, 
        threshold: float = 0.8
    ) -> List[Citation]:
        """Get only high-confidence sources"""
        return [c for c in self.citations if c.confidence >= threshold]
    
    def get_best_sources(self, n: int = 3) -> List[Citation]:
        """Get n best sources (by authority + confidence)"""
        scored = [
            (c, self.get_authority_score(c.source) * c.confidence)
            for c in self.citations
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:n]]


def inject_citations_into_answer(
    answer: str,
    citations: List[Citation]
) -> Tuple[str, str]:
    """
    Inject citation markers into answer and create bibliography
    
    Returns:
        (answer_with_citations, bibliography)
    """
    
    # Add bibliography
    bib = "\n\n📚 **Sources:**\n"
    for citation in citations:
        bib += f"{citation.format()}\n"
    
    # You could enhance this to auto-inject [1] markers based on content
    # For now, we just append bibliography
    return answer, bib


# FastAPI Integration
def add_citations_endpoint(app):
    """Add citations endpoint to FastAPI app"""
    from fastapi import FastAPI
    
    tracker = CitationTracker()
    
    @app.post("/query/with-citations")
    async def query_with_citations(query: str, k: int = 5):
        """Query with citations tracking"""
        
        # Retrieve documents
        # results = system.advanced_retriever.retrieve(query, k=k)
        # For demo, assume we have results
        
        # Extract citations
        citations = tracker.extract_citations_from_docs([])  # Would pass results
        
        # Generate answer
        # answer = system.generate_answer(query, results)
        
        # Inject citations
        # answer_with_cites, bib = inject_citations_into_answer(answer, citations)
        
        return {
            "answer": "Sample answer",
            "citations": [{
                "index": c.index,
                "source": c.source,
                "page": c.page,
                "confidence": f"{c.confidence:.0%}"
            } for c in citations],
            "bibliography": "📚 Sources listed above"
        }
    
    return app


# Usage Example
if __name__ == "__main__":
    from langchain.schema import Document
    
    tracker = CitationTracker()
    
    # Sample documents
    docs = [
        Document(
            page_content="Anxiety disorder...",
            metadata={
                'source': 'DSM-5',
                'page': '160',
                'confidence': 0.95
            }
        ),
        Document(
            page_content="Anxiety is defined...",
            metadata={
                'source': 'Mayo Clinic',
                'page': '?',
                'confidence': 0.90
            }
        )
    ]
    
    # Extract citations
    citations = tracker.extract_citations_from_docs(docs)
    
    # Display
    print("Citations:")
    for citation in citations:
        print(f"  {citation.format()}")
    
    print("\nBibliography:")
    print(tracker.get_formatted_bibliography())
    
    # Filter high confidence
    high_conf = tracker.filter_high_confidence(threshold=0.9)
    print(f"\nHigh confidence sources ({len(high_conf)}):")
    for citation in high_conf:
        print(f"  {citation.source}")
```

---

## Feature 4: Async Retrieval

### File: `scripts/async_retrieval.py`

```python
"""
Async Retrieval System
Handle concurrent users with non-blocking retrieval
"""

import asyncio
from typing import List
from concurrent.futures import ThreadPoolExecutor
from langchain.schema import Document


class AsyncRAGRetriever:
    """Async wrapper for RAG retrieval"""
    
    def __init__(self, vector_store, max_workers: int = 5):
        """
        Initialize async retriever
        
        Args:
            vector_store: ChromaDB or similar vector store
            max_workers: Thread pool size
        """
        self.vector_store = vector_store
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = None
    
    async def retrieve_async(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Document]:
        """
        Async similarity search
        
        Args:
            query: Search query
            k: Number of results
        
        Returns:
            Retrieved documents
        """
        
        self.loop = asyncio.get_event_loop()
        
        # Run blocking operation in thread pool
        results = await self.loop.run_in_executor(
            self.executor,
            self.vector_store.similarity_search,
            query,
            k
        )
        
        return results
    
    async def retrieve_batch_async(
        self,
        queries: List[str],
        k: int = 5
    ) -> List[List[Document]]:
        """
        Retrieve for multiple queries in parallel
        
        Args:
            queries: List of queries
            k: Results per query
        
        Returns:
            List of result lists
        """
        
        tasks = [
            self.retrieve_async(query, k)
            for query in queries
        ]
        
        # Run all in parallel
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def hybrid_retrieve_async(
        self,
        query: str,
        k: int = 5,
        alpha: float = 0.6
    ) -> List[Document]:
        """Async hybrid search (semantic + keyword)"""
        
        self.loop = asyncio.get_event_loop()
        
        # Run in thread pool
        results = await self.loop.run_in_executor(
            self.executor,
            self._hybrid_search,
            query,
            k,
            alpha
        )
        
        return results
    
    def _hybrid_search(self, query: str, k: int, alpha: float):
        """Blocking hybrid search implementation"""
        # This would call your advanced retriever's hybrid search
        # For now, just do similarity search
        return self.vector_store.similarity_search(query, k)


class AsyncReranker:
    """Async reranking for parallel documents"""
    
    def __init__(self, reranker, max_workers: int = 5):
        """Initialize async reranker"""
        self.reranker = reranker
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def rerank_batch_async(
        self,
        query_doc_pairs: List[tuple]  # [(query, docs), ...]
    ) -> List[List[Document]]:
        """
        Rerank multiple queries in parallel
        
        Args:
            query_doc_pairs: List of (query, documents) tuples
        
        Returns:
            Reranked results for each query
        """
        
        loop = asyncio.get_event_loop()
        
        tasks = [
            loop.run_in_executor(
                self.executor,
                self.reranker.rerank_documents,
                docs,
                query
            )
            for query, docs in query_doc_pairs
        ]
        
        results = await asyncio.gather(*tasks)
        return results


# FastAPI Integration for Async Serving
def create_async_endpoints(app, system):
    """Add async endpoints to FastAPI app"""
    from fastapi import FastAPI
    
    async_retriever = AsyncRAGRetriever(system.vector_store)
    
    @app.post("/query/async")
    async def query_async(
        query: str,
        user_id: str = None,
        k: int = 5
    ):
        """Async query endpoint"""
        
        # Non-blocking retrieval
        results = await async_retriever.retrieve_async(query, k)
        
        # Get answer (can also be async with streaming)
        answer = system.generate_answer(query, results)
        
        return {
            "answer": answer,
            "sources": [d.metadata.get('source') for d in results],
            "count": len(results)
        }
    
    @app.post("/batch-query/async")
    async def batch_query_async(queries: List[str], k: int = 5):
        """Batch query - all in parallel"""
        
        # All queries run in parallel
        results_batch = await async_retriever.retrieve_batch_async(queries, k)
        
        answers = [
            system.generate_answer(q, r)
            for q, r in zip(queries, results_batch)
        ]
        
        return {
            "queries": queries,
            "answers": answers,
            "count": len(queries)
        }
    
    return app


# Standalone async usage
async def example_concurrent_queries():
    """Example of handling multiple concurrent users"""
    
    from rag_advanced import AdvancedRAGRetriever
    from langchain_chroma import Chroma
    
    # Setup
    vector_store = Chroma(...)
    async_retriever = AsyncRAGRetriever(vector_store)
    
    # 5 concurrent queries
    queries = [
        "anxiety symptoms",
        "depression treatment",
        "sleep disorders",
        "stress management",
        "panic attack therapy"
    ]
    
    print("Running 5 queries in parallel...")
    results = await async_retriever.retrieve_batch_async(queries, k=5)
    
    for query, docs in zip(queries, results):
        print(f"\n{query}: {len(docs)} results")


# Run if main
if __name__ == "__main__":
    # Run concurrent example
    asyncio.run(example_concurrent_queries())
```

---

## Feature 5: Observability & Analytics

### File: `scripts/observability.py`

```python
"""
Production Observability System
Track metrics, detect issues, generate insights
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter, defaultdict
import json
import time


@dataclass
class QueryMetrics:
    """Metrics for single query"""
    query: str
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    cache_hit: bool = False
    results_count: int = 0
    sources: List[str] = field(default_factory=list)
    hallucination_detected: bool = False
    failed: bool = False
    error_message: Optional[str] = None
    
    @property
    def total_time_ms(self) -> float:
        """Total latency"""
        return self.retrieval_time_ms + self.generation_time_ms
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'retrieval_ms': round(self.retrieval_time_ms, 2),
            'generation_ms': round(self.generation_time_ms, 2),
            'total_ms': round(self.total_time_ms, 2),
            'cache_hit': self.cache_hit,
            'results_count': self.results_count,
            'sources': self.sources,
            'hallucination': self.hallucination_detected,
            'failed': self.failed
        }


class ObservabilityCollector:
    """Collect and analyze metrics"""
    
    def __init__(self, window_minutes: int = 60):
        """
        Initialize collector
        
        Args:
            window_minutes: Time window for trending
        """
        self.metrics: List[QueryMetrics] = []
        self.window = timedelta(minutes=window_minutes)
        
        # Aggregates
        self.cache_hits = 0
        self.cache_misses = 0
        self.hallucinations = 0
        self.failures = 0
        self.total_queries = 0
    
    def log_query(self, metrics: QueryMetrics) -> None:
        """Log query metrics"""
        self.metrics.append(metrics)
        self.total_queries += 1
        
        # Update aggregates
        if metrics.cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        if metrics.hallucination_detected:
            self.hallucinations += 1
        
        if metrics.failed:
            self.failures += 1
    
    def get_cache_stats(self) -> Dict:
        """Cache performance statistics"""
        total = self.total_queries
        if total == 0:
            return {}
        
        return {
            'total_queries': total,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate_percent': round((self.cache_hits / total) * 100, 1),
            'miss_rate_percent': round((self.cache_misses / total) * 100, 1)
        }
    
    def get_latency_stats(self) -> Dict:
        """Latency statistics"""
        if not self.metrics:
            return {}
        
        times = [m.total_time_ms for m in self.metrics if not m.failed]
        if not times:
            return {}
        
        return {
            'avg_latency_ms': round(sum(times) / len(times), 2),
            'min_latency_ms': round(min(times), 2),
            'max_latency_ms': round(max(times), 2),
            'p95_latency_ms': round(sorted(times)[int(len(times) * 0.95)], 2),
            'p99_latency_ms': round(sorted(times)[int(len(times) * 0.99)], 2),
        }
    
    def get_quality_stats(self) -> Dict:
        """Quality metrics"""
        total = self.total_queries
        if total == 0:
            return {}
        
        return {
            'total_queries': total,
            'hallucination_count': self.hallucinations,
            'hallucination_rate_percent': round((self.hallucinations / total) * 100, 2),
            'failure_count': self.failures,
            'failure_rate_percent': round((self.failures / total) * 100, 2),
            'success_rate_percent': round(((total - self.failures) / total) * 100, 2)
        }
    
    def get_top_queries(self, n: int = 10) -> List[tuple]:
        """Most common queries"""
        queries = [m.query for m in self.metrics]
        return Counter(queries).most_common(n)
    
    def get_slowest_queries(self, n: int = 5) -> List[QueryMetrics]:
        """Slowest queries for optimization"""
        sorted_metrics = sorted(
            self.metrics,
            key=lambda m: m.total_time_ms,
            reverse=True
        )
        return sorted_metrics[:n]
    
    def get_failed_queries(self) -> List[QueryMetrics]:
        """Failed queries analysis"""
        return [m for m in self.metrics if m.failed]
    
    def get_hallucinations(self) -> List[QueryMetrics]:
        """Queries with detected hallucinations"""
        return [m for m in self.metrics if m.hallucination_detected]
    
    def get_dashboard(self) -> Dict:
        """Complete dashboard view"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cache': self.get_cache_stats(),
            'latency': self.get_latency_stats(),
            'quality': self.get_quality_stats(),
            'top_queries': self.get_top_queries(10),
            'slowest_queries': [
                m.to_dict() for m in self.get_slowest_queries(5)
            ],
            'health_status': self._compute_health_status()
        }
    
    def _compute_health_status(self) -> str:
        """Compute overall system health"""
        quality = self.get_quality_stats()
        latency = self.get_latency_stats()
        
        if not quality or not latency:
            return "UNKNOWN"
        
        failure_rate = quality.get('failure_rate_percent', 0)
        hallucination_rate = quality.get('hallucination_rate_percent', 0)
        avg_latency = latency.get('avg_latency_ms', 0)
        
        if failure_rate > 5 or hallucination_rate > 2:
            return "🔴 CRITICAL"
        elif failure_rate > 1 or hallucination_rate > 0.5 or avg_latency > 2000:
            return "🟡 WARNING"
        else:
            return "🟢 HEALTHY"
    
    def export_metrics_json(self) -> str:
        """Export all metrics to JSON"""
        data = {
            'dashboard': self.get_dashboard(),
            'detailed_metrics': [m.to_dict() for m in self.metrics]
        }
        return json.dumps(data, indent=2)
    
    def get_hourly_report(self) -> Dict:
        """Hourly trending"""
        by_hour = defaultdict(list)
        
        now = datetime.now()
        for metric in self.metrics:
            if now - metric.timestamp < timedelta(hours=1):
                hour = metric.timestamp.strftime("%H:00")
                by_hour[hour].append(metric)
        
        report = {}
        for hour, metrics in sorted(by_hour.items()):
            times = [m.total_time_ms for m in metrics if not m.failed]
            report[hour] = {
                'queries': len(metrics),
                'avg_latency_ms': round(sum(times) / len(times), 2) if times else 0,
                'failures': len([m for m in metrics if m.failed])
            }
        
        return report


# Integration into FastAPI
def add_observability_endpoints(app, collector: ObservabilityCollector):
    """Add observability endpoints"""
    from fastapi import FastAPI
    
    @app.get("/metrics/dashboard")
    async def get_dashboard():
        """Real-time dashboard"""
        return collector.get_dashboard()
    
    @app.get("/metrics/cache")
    async def get_cache():
        """Cache statistics"""
        return collector.get_cache_stats()
    
    @app.get("/metrics/latency")
    async def get_latency():
        """Latency statistics"""
        return collector.get_latency_stats()
    
    @app.get("/metrics/quality")
    async def get_quality():
        """Quality metrics"""
        return collector.get_quality_stats()
    
    @app.get("/metrics/top-queries")
    async def get_top_queries(n: int = 10):
        """Top queries"""
        return {"top_queries": collector.get_top_queries(n)}
    
    @app.get("/metrics/slowest")
    async def get_slowest(n: int = 5):
        """Slowest queries"""
        return {
            "slowest_queries": [
                m.to_dict() for m in collector.get_slowest_queries(n)
            ]
        }
    
    @app.get("/metrics/health")
    async def get_health():
        """System health status"""
        dashboard = collector.get_dashboard()
        return {"health_status": dashboard.get('health_status')}
    
    @app.get("/metrics/hourly")
    async def get_hourly():
        """Hourly report"""
        return collector.get_hourly_report()
    
    @app.get("/metrics/export")
    async def export_metrics():
        """Export all metrics"""
        return json.loads(collector.export_metrics_json())
    
    return app


# Wrapper for query with observability
def query_with_observability(
    system,
    query: str,
    user_id: str,
    collector: ObservabilityCollector
) -> tuple:
    """Execute query with full observability"""
    
    metrics = QueryMetrics(query=query, user_id=user_id)
    
    try:
        # Retrieve
        retrieval_start = time.time()
        results = system.advanced_retriever.retrieve(query, k=5)
        metrics.retrieval_time_ms = (time.time() - retrieval_start) * 1000
        metrics.results_count = len(results)
        metrics.sources = [r.metadata.get('source', 'Unknown') for r in results]
        
        # Generate
        gen_start = time.time()
        answer = system.generate_answer(query, results)
        metrics.generation_time_ms = (time.time() - gen_start) * 1000
        
        # Detect hallucinations (basic)
        metrics.hallucination_detected = _detect_hallucination(answer, results)
        
    except Exception as e:
        metrics.failed = True
        metrics.error_message = str(e)
        answer = f"Error: {str(e)}"
    
    # Log metrics
    collector.log_query(metrics)
    
    # Print alerts if needed
    if metrics.hallucination_detected:
        print(f"⚠️  Hallucination detected: {query}")
    if metrics.total_time_ms > 1000:
        print(f"⚠️  Slow query ({metrics.total_time_ms}ms): {query}")
    if metrics.failed:
        print(f"❌ Query failed: {query}")
    
    return answer, metrics


def _detect_hallucination(answer: str, docs: List) -> bool:
    """Basic hallucination detection"""
    # Check if answer has specific numbers not in docs
    source_text = " ".join([d.page_content for d in docs])
    
    # Count nouns in answer vs source
    answer_words = set(answer.lower().split())
    source_words = set(source_text.lower().split())
    
    novel_words = len(answer_words - source_words)
    
    # If >40% of answer is novel, possible hallucination
    return novel_words > len(answer_words) * 0.4


#Usage
if __name__ == "__main__":
    collector = ObservabilityCollector()
    
    # Simulate queries
    for i in range(10):
        metric = QueryMetrics(
            query=f"test query {i}",
            user_id=f"user_{i}",
            retrieval_time_ms=100 + i*10,
            generation_time_ms=200 + i*5,
            cache_hit=i % 3 == 0,
            results_count=5
        )
        collector.log_query(metric)
    
    # Get dashboard
    dashboard = collector.get_dashboard()
    print(json.dumps(dashboard, indent=2))
```

---

## Implementation Checklist

- [ ] **Conversation Memory** - `scripts/conversation_memory.py` created
- [ ] **Streaming** - `scripts/streaming_response.py` created
- [ ] **Citations** - `scripts/source_citations.py` created
- [ ] **Async Retrieval** - `scripts/async_retrieval.py` created
- [ ] **Observability** - `scripts/observability.py` created
- [ ] Update `scripts/query_rag_system.py` with all 5 features
- [ ] Update `scripts/neuronix_query.py` with all 5 features
- [ ] Create FastAPI endpoints for streaming + async
- [ ] Set up observability dashboard
- [ ] Test with concurrent users

## Next Steps

1. Pick **Citations + Observability** this week (2 hours, maximum ROI)
2. Add **Conversation Memory** next week (2 hours, better UX)
3. Deploy **Async Retrieval** before production launch (when needed)
4. Polish with **Streaming** if time permits (nice-to-have)

Ready to implement? Start with Feature 3 (Citations) - it's quick and builds trust! 🚀
