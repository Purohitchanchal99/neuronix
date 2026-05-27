#!/usr/bin/env python3
"""
Phase 2 Interactive Demo
========================
Try Phase 2 responses with real queries

Usage:
  python scripts/PHASE2_DEMO.py
  
Then try:
  - "I feel anxious all the time"
  - "Why do I feel depressed and what can I do?"
  - "What is CBT?"
  - "I can't take this anymore"
  - (Enter 'quit' to exit)
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from response_quality_engine import ResponseQualityEngine


def print_banner():
    print("\n" + "=" * 80)
    print("PHASE 2: RESPONSE QUALITY ENGINE - INTERACTIVE DEMO")
    print("=" * 80)
    print("\nTry asking about:")
    print("  • Mental health concerns (anxiety, depression, stress, etc.)")
    print("  • Clinical questions (What is therapy? How does CBT work?)")
    print("  • General questions (Hello! How are you?)")
    print("\nType 'quit' or 'exit' to leave")
    print("Type 'compare' to see before/after comparison")
    print("=" * 80 + "\n")


def print_response_details(result):
    """Pretty print response with analysis"""
    print("\n" + "─" * 80)
    print("RESPONSE:")
    print("─" * 80)
    print(result["response"])
    
    print("\n" + "─" * 80)
    print("ANALYSIS:")
    print("─" * 80)
    print(f"Tone:           {result['tone'].upper()}")
    print(f"Distress Level: {result['distress_level']:.0%}")
    print(f"Confidence:     {result['confidence']:.0%}")
    if result['keywords']:
        print(f"Keywords:       {', '.join(result['keywords'])}")
    print(f"Crisis Detected: {'YES' if result['is_crisis'] else 'No'}")
    print("─" * 80 + "\n")


def print_comparison(query, context=""):
    """Show before/after comparison"""
    engine = ResponseQualityEngine()
    comparison = engine.compare_old_vs_new(query, context)
    
    print("\n" + "=" * 80)
    print("BEFORE vs AFTER COMPARISON")
    print("=" * 80)
    
    print(f"\nQuery: \"{query}\"")
    print(f"\n❌ OLD (v1.5 - Robotic):")
    print("─" * 80)
    print(comparison['old_response'])
    
    print(f"\n✅ NEW (Phase 2 - Human-like):")
    print("─" * 80)
    print(comparison['new_response'])
    
    print(f"\n📊 IMPROVEMENTS:")
    print("─" * 80)
    print(f"Tone Detected: {comparison['tone_detected']}")
    print(f"Distress Level: {comparison['distress_level']:.0%}")
    print("\nPhase 2 Features Active:")
    for improvement in comparison['improvements']:
        print(f"  {improvement}")
    print("=" * 80 + "\n")


def main():
    """Interactive demo loop"""
    
    engine = ResponseQualityEngine()
    print_banner()
    
    query_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                print("(please enter something)")
                continue
            
            # Check for special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n✅ Thanks for trying Phase 2! Goodbye! 👋\n")
                break
            
            if user_input.lower() == 'compare':
                compare_query = input("Enter query to compare: ").strip()
                if compare_query:
                    print_comparison(compare_query)
                continue
            
            # Process query
            result = engine.build_response(user_input)
            query_count += 1
            
            # Display response with analysis
            print_response_details(result)
            
            # Show tips after a few queries
            if query_count == 3:
                print("\n💡 TIP: Type 'compare' to see before/after comparison for any query")
            
        except KeyboardInterrupt:
            print("\n\n✅ Thanks for trying Phase 2! Goodbye! 👋\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try another query.\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
