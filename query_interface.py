#!/usr/bin/env python3
"""
NEURONIX QUERY INTERFACE
========================
Test the complete RAG system end-to-end

Usage:
    python query_interface.py --query "I feel anxious"
    python query_interface.py --interactive
"""

import sys
import os
import argparse
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "scripts")))

from scripts.neuronix_ingest import NeuronixIngestion
from scripts.neuronix_core import NeuronixCore
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_system():
    """Initialize vector store and core processor"""
    logger.info("\n" + "="*80)
    logger.info("🚀 NEURONIX QUERY SYSTEM - Initializing")
    logger.info("="*80)
    
    # Initialize ingestion engine (for vector store access)
    logger.info("\n📦 Loading vector store...")
    ingestion = NeuronixIngestion()
    ingestion.initialize_vector_store()
    
    # Initialize core processor (no LLM - templates mode)
    logger.info("🧠 Initializing NEURONIX CORE...")
    core = NeuronixCore(ingestion.vector_store, llm=None)
    
    logger.info(f"✅ System ready: {core.get_stats()}")
    
    return core, ingestion


def format_result(result):
    """Format query result for display"""
    output = []
    output.append("\n" + "="*80)
    
    if result.status == "crisis":
        output.append("🚨 CRISIS RESPONSE")
    elif result.status == "error":
        output.append("❌ ERROR")
    else:
        output.append("✅ RESPONSE")
    
    output.append("="*80)
    output.append(f"\nRisk Level: {result.risk_level.upper()}")
    output.append(f"\n{result.response}")
    
    if result.source_chunks:
        output.append(f"\n\n📚 Sources ({len(result.source_chunks)} chunks):")
        for i, chunk in enumerate(result.source_chunks, 1):
            source = chunk['source']
            topics = ", ".join(chunk['topics'][:2]) if chunk['topics'] else "N/A"
            output.append(f"   [{i}] {source} (Topics: {topics})")
    
    output.append("\n" + "="*80 + "\n")
    
    return "\n".join(output)


def single_query_mode(core, query):
    """Handle single query mode"""
    logger.info(f"\n📨 Processing query: {query}")
    
    result = core.handle_query(query)
    print(format_result(result))
    
    return result.status == "success" or result.status == "crisis"


def interactive_mode(core):
    """Interactive query loop"""
    print("\n" + "="*80)
    print("💬 INTERACTIVE MODE")
    print("="*80)
    print("\nCommands:")
    print("  'quit' or 'exit' - Exit")
    print("  'status' - System status")
    print("  anything else - Ask NEURONIX")
    print("\n" + "="*80 + "\n")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Goodbye!")
                break
            
            if user_input.lower() == 'status':
                stats = core.get_stats()
                print(f"\n📊 System Status:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                continue
            
            # Process query
            result = core.handle_query(user_input)
            print(format_result(result))
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in interactive mode: {e}")
            print(f"❌ Error: {e}")


def demo_queries(core):
    """Run demo queries to showcase system"""
    demo_tests = [
        ("I feel so anxious I can't leave my apartment", "Anxiety scenario"),
        ("I feel hopeless and nothing matters anymore", "Distress scenario"),
        ("I'm thinking about ending my life", "Crisis scenario - HIGH RISK"),
        ("What are some therapies for depression?", "Educational query"),
        ("How can I sleep better?", "Sleep issue"),
    ]
    
    logger.info("\n" + "="*80)
    logger.info("🎬 DEMO MODE - Testing Sample Queries")
    logger.info("="*80)
    
    for query, description in demo_tests:
        print(f"\n{'='*80}")
        print(f"📝 Test: {description}")
        print(f"{'='*80}")
        print(f"Q: {query}\n")
        
        result = core.handle_query(query)
        print(f"A: {result.response}")
        
        if result.source_chunks:
            print(f"\n📚 Sources:")
            for i, chunk in enumerate(result.source_chunks, 1):
                print(f"   [{i}] {chunk['source']}")
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description="NEURONIX Query Interface - RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single query:
    python query_interface.py --query "How do I deal with anxiety?"
  
  Interactive mode:
    python query_interface.py --interactive
  
  Demo mode:
    python query_interface.py --demo
        """
    )
    
    parser.add_argument("--query", type=str, help="Single query to process")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--demo", action="store_true", help="Run demo queries")
    
    args = parser.parse_args()
    
    # Initialize system
    try:
        core, ingestion = initialize_system()
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        return 1
    
    # Route to appropriate mode
    if args.query:
        success = single_query_mode(core, args.query)
        return 0 if success else 1
    
    elif args.interactive:
        interactive_mode(core)
        return 0
    
    elif args.demo:
        demo_queries(core)
        return 0
    
    else:
        # Default to interactive
        interactive_mode(core)
        return 0


if __name__ == "__main__":
    sys.exit(main())
