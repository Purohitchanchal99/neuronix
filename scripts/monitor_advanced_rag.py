#!/usr/bin/env python3
"""
Advanced RAG Monitoring & Statistics
=====================================
Monitor cache performance, retrieval quality, and system health

Features:
- Real-time cache statistics
- Retrieval performance tracking
- Hybrid search effectiveness analysis
- Query pattern insights
- System health dashboard

Usage:
  from monitor_advanced_rag import RAGMonitor
  
  monitor = RAGMonitor()
  
  # Get current statistics
  stats = monitor.get_cache_stats(retriever)
  print(f"Cache hit rate: {stats['hit_rate_percent']}%")
  
  # Track queries over time
  monitor.log_query(query, results_count, retrieval_time)
  
  # Get insights
  insights = monitor.get_insights()
  print(insights)
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RAGMonitor:
    """Monitor Advanced RAG system performance"""
    
    def __init__(self, log_dir: Optional[Path] = None, window_size: int = 1000):
        """
        Initialize monitor
        
        Args:
            log_dir: Directory for monitoring logs (default: same as script)
            window_size: Number of queries to track (default: 1000)
        """
        self.log_dir = log_dir or Path(__file__).parent.parent / "monitoring"
        self.log_dir.mkdir(exist_ok=True)
        
        self.window_size = window_size
        self.query_history = deque(maxlen=window_size)
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_retrieval_time = 0.0
        
        # Performance by hour
        self.hourly_stats = defaultdict(lambda: {
            'queries': 0,
            'cache_hits': 0,
            'avg_retrieval_time': 0.0
        })
        
        # Query patterns
        self.query_patterns = defaultdict(int)
        self.topic_distribution = defaultdict(int)
        
        logger.info(f"📊 RAG Monitor initialized (window: {window_size} queries)")
    
    def get_cache_stats(self, retriever) -> Dict:
        """
        Get cache statistics from retriever
        
        Args:
            retriever: AdvancedRAGRetriever instance
            
        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = retriever.get_stats()
            cache_stats = stats.get('cache', {})
            
            return {
                'hit_rate_percent': cache_stats.get('hit_rate_percent', 0),
                'cache_entries': cache_stats.get('entries', 0),
                'cache_size': cache_stats.get('cache_size', 0),
                'hits': cache_stats.get('hits', 0),
                'misses': cache_stats.get('misses', 0),
            }
        except Exception as e:
            logger.warning(f"⚠️  Could not get cache stats: {e}")
            return {
                'hit_rate_percent': 0,
                'cache_entries': 0,
                'cache_size': 0,
                'hits': 0,
                'misses': 0,
                'error': str(e)
            }
    
    def get_hybrid_stats(self, retriever) -> Dict:
        """Get hybrid search statistics"""
        try:
            stats = retriever.get_stats()
            hybrid_stats = stats.get('hybrid', {})
            
            return {
                'enabled': hybrid_stats.get('enabled', False),
                'alpha': hybrid_stats.get('alpha', 0),
                'keyword_searches': hybrid_stats.get('keyword_searches', 0),
                'semantic_searches': hybrid_stats.get('semantic_searches', 0),
            }
        except Exception as e:
            logger.warning(f"⚠️  Could not get hybrid stats: {e}")
            return {'enabled': False, 'error': str(e)}
    
    def log_query(
        self,
        query: str,
        results_count: int,
        retrieval_time: float,
        cache_hit: bool = False,
        topics: Optional[List[str]] = None
    ):
        """
        Log query for monitoring
        
        Args:
            query: Query text
            results_count: Number of results returned
            retrieval_time: Time taken for retrieval (seconds)
            cache_hit: Whether result was cached
            topics: List of topics detected in query
        """
        entry = {
            'timestamp': datetime.now(),
            'query': query,
            'results_count': results_count,
            'retrieval_time': retrieval_time,
            'cache_hit': cache_hit,
            'topics': topics or []
        }
        
        self.query_history.append(entry)
        
        # Update statistics
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1
        
        self.total_retrieval_time += retrieval_time
        
        # Update hourly stats
        hour_key = entry['timestamp'].strftime('%Y-%m-%d %H:00')
        self.hourly_stats[hour_key]['queries'] += 1
        if cache_hit:
            self.hourly_stats[hour_key]['cache_hits'] += 1
        
        # Track topics
        for topic in (topics or []):
            self.topic_distribution[topic] += 1
        
        # Track query patterns
        query_lower = query.lower()
        if 'anxiety' in query_lower:
            self.query_patterns['anxiety'] += 1
        elif 'depression' in query_lower:
            self.query_patterns['depression'] += 1
        elif 'stress' in query_lower:
            self.query_patterns['stress'] += 1
        elif 'sleep' in query_lower:
            self.query_patterns['sleep'] += 1
        else:
            self.query_patterns['other'] += 1
    
    def get_hourly_report(self) -> Dict:
        """Get performance by hour"""
        report = {}
        
        for hour, stats in sorted(self.hourly_stats.items()):
            queries = stats['queries']
            hits = stats['cache_hits']
            
            if queries > 0:
                cache_hit_rate = (hits / queries) * 100
                avg_time = stats.get('avg_retrieval_time', 0)
            else:
                cache_hit_rate = 0
                avg_time = 0
            
            report[hour] = {
                'queries': queries,
                'cache_hits': hits,
                'hit_rate_percent': round(cache_hit_rate, 1),
                'avg_retrieval_time': round(avg_time, 3)
            }
        
        return report
    
    def get_insights(self) -> str:
        """
        Generate insights about system performance
        
        Returns:
            Formatted string with insights
        """
        total_queries = self.cache_hits + self.cache_misses
        
        if total_queries == 0:
            return "📊 No queries logged yet"
        
        cache_hit_rate = (self.cache_hits / total_queries) * 100
        avg_time = self.total_retrieval_time / total_queries if total_queries > 0 else 0
        
        insights = []
        insights.append(f"\n{'='*70}")
        insights.append(f"📊 ADVANCED RAG PERFORMANCE INSIGHTS")
        insights.append(f"{'='*70}\n")
        
        # Cache performance
        insights.append(f"💾 Cache Performance:")
        insights.append(f"   • Total queries: {total_queries}")
        insights.append(f"   • Cache hits: {self.cache_hits}")
        insights.append(f"   • Cache misses: {self.cache_misses}")
        insights.append(f"   • Hit rate: {cache_hit_rate:.1f}%")
        
        # Retrieval performance
        insights.append(f"\n⚡ Retrieval Performance:")
        insights.append(f"   • Avg retrieval time: {avg_time:.3f}s")
        insights.append(f"   • Total retrieval time: {self.total_retrieval_time:.1f}s")
        
        # Cache quality
        if cache_hit_rate >= 50:
            insights.append(f"\n✅ Good cache performance! Hit rate is {cache_hit_rate:.1f}%")
            insights.append(f"   Recommendation: Cache is effective, consider increasing cache_size")
        elif cache_hit_rate >= 30:
            insights.append(f"\n🟡 Moderate cache performance. Hit rate is {cache_hit_rate:.1f}%")
            insights.append(f"   Recommendation: Monitor further, may increase with more usage")
        else:
            insights.append(f"\n⚠️  Low cache hit rate. Only {cache_hit_rate:.1f}%")
            insights.append(f"   Recommendation: Queries are diverse, cache helps less common questions")
        
        # Query patterns
        if self.query_patterns:
            insights.append(f"\n🎯 Query Patterns:")
            top_pattern = max(self.query_patterns.items(), key=lambda x: x[1])
            insights.append(f"   • Most common: {top_pattern[0]} ({top_pattern[1]} queries)")
            
            for pattern, count in sorted(
                self.query_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]:
                insights.append(f"     - {pattern}: {count}")
        
        # Topic distribution
        if self.topic_distribution:
            insights.append(f"\n📚 Topic Distribution:")
            top_topic = max(self.topic_distribution.items(), key=lambda x: x[1])
            insights.append(f"   • Most queried: {top_topic[0]}")
        
        insights.append(f"\n{'='*70}\n")
        
        return "\n".join(insights)
    
    def export_stats(self, filepath: Optional[Path] = None) -> Dict:
        """
        Export all statistics to JSON
        
        Args:
            filepath: Where to save stats (default: monitoring dir)
            
        Returns:
            Dictionary of all statistics
        """
        filepath = filepath or (self.log_dir / f"rag_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        total_queries = self.cache_hits + self.cache_misses
        
        stats_dict = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_queries': total_queries,
                'cache_hits': self.cache_hits,
                'cache_misses': self.cache_misses,
                'hit_rate_percent': round((self.cache_hits / total_queries * 100) if total_queries > 0 else 0, 1),
                'avg_retrieval_time': round(self.total_retrieval_time / total_queries if total_queries > 0 else 0, 3)
            },
            'hourly_report': self.get_hourly_report(),
            'query_patterns': dict(self.query_patterns),
            'topic_distribution': dict(self.topic_distribution),
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Statistics exported to {filepath}")
        except Exception as e:
            logger.error(f"❌ Failed to export stats: {e}")
        
        return stats_dict
    
    def print_dashboard(self, retriever=None):
        """
        Print live dashboard
        
        Args:
            retriever: AdvancedRAGRetriever instance (optional, for live stats)
        """
        print(self.get_insights())
        
        if retriever:
            print("\n📈 Live Cache Statistics:")
            cache_stats = self.get_cache_stats(retriever)
            for key, value in cache_stats.items():
                if key != 'error':
                    print(f"   • {key}: {value}")
            
            print("\n🔀 Hybrid Search Statistics:")
            hybrid_stats = self.get_hybrid_stats(retriever)
            for key, value in hybrid_stats.items():
                if key != 'error':
                    print(f"   • {key}: {value}")


# ================================================================
# EXAMPLE USAGE
# ================================================================

if __name__ == "__main__":
    print("📊 Advanced RAG Monitor Demo\n")
    
    monitor = RAGMonitor()
    
    print("Simulating queries...")
    
    # Simulate queries
    queries = [
        ("what causes anxiety?", 5, 0.15, False),
        ("anxiety symptoms", 5, 0.05, True),
        ("depression treatment", 6, 0.18, False),
        ("anxiety symptoms", 5, 0.03, True),
        ("sleep problems", 5, 0.16, False),
        ("anxiety attacks", 5, 0.04, True),
        ("stress management", 5, 0.17, False),
        ("anxiety symptoms", 5, 0.02, True),
        ("panic disorder", 5, 0.19, False),
        ("anxiety relief", 5, 0.06, True),
    ]
    
    for i, (query, results, time_taken, cache_hit) in enumerate(queries):
        monitor.log_query(query, results, time_taken, cache_hit)
        print(f"  [{i+1}] {query} - {'💾 CACHE' if cache_hit else '🔍 MISS'}")
    
    print("\n" + monitor.get_insights())
    
    # Export
    stats = monitor.export_stats()
    print(f"✅ Statistics exported")
