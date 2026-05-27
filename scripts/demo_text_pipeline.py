#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 TEXT CLEANING PIPELINE - QUICK START DEMO
==============================================

Shows all 6 components in action:
1. Cleaning - Remove noise
2. Chunking - Smart segmentation
3. Metadata - Auto-generate info
4. Q&A - Generate questions
5. Safety - Mental health checks
6. Integration - Store in ChromaDB
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.text_cleaner_pipeline import (
    TextProcessingPipeline,
    TextCleaner,
    SmartChunker,
    MetadataGenerator,
    QAGenerator,
    SafetyChecker,
)
import json


def demo_text_cleaner():
    """Demo 1: Show text cleaning in action"""
    
    print("\n" + "="*80)
    print("DEMO 1: TEXT CLEANING")
    print("="*80)
    
    # Sample messy PDF text
    messy_text = """
    Clinical Psychology in Practice
    
    Page 42
    
    Anxiety    disorders    are    among    the    most    common    mental    health    conditions.
    Research    shows    that    approximately    19%    of    the    population-
    experiences    an    anxiety    disorder    annually.
    
    Page 43
    
    Treatment    approaches    include    cognitive-behavioral    therapy    (CBT),    medications,
    and    lifestyle    changes.    The    efficacy    of    psy-
    chological    interventions    has    been    well    documented
    in    numerous    studies.
    """
    
    cleaner = TextCleaner()
    cleaned = cleaner.clean(messy_text)
    stats = cleaner.get_stats()
    
    print("\n📥 BEFORE (Messy):")
    print(repr(messy_text[:200]))
    
    print("\n📤 AFTER (Clean):")
    print(repr(cleaned[:200]))
    
    print("\n📊 Cleaning Stats:")
    for key, value in stats.items():
        if key != 'input_chars' and key != 'output_chars':
            print(f"  • {key}: {value}")
    print(f"  • Size reduction: {stats['input_chars']} → {stats['output_chars']} chars")


def demo_chunking():
    """Demo 2: Show smart chunking"""
    
    print("\n" + "="*80)
    print("DEMO 2: SMART CHUNKING")
    print("="*80)
    
    sample_text = """
    Chapter 1: Understanding Depression
    
    Depression is a complex mental health condition characterized by persistent sad mood, 
    loss of interest in activities, changes in appetite and sleep patterns, and feelings 
    of worthlessness or guilt. It affects millions of people worldwide and can significantly 
    impact daily functioning.
    
    Chapter 2: Treatment Approaches
    
    Treatment for depression typically involves a combination of psychotherapy and medication. 
    Cognitive-behavioral therapy has shown high efficacy in treating depressive episodes. 
    Selective serotonin reuptake inhibitors are commonly prescribed as first-line medications.
    
    Chapter 3: Recovery and Prevention
    
    Recovery from depression is possible with appropriate treatment and support. Regular 
    exercise, social connection, and healthy sleep patterns contribute to long-term recovery. 
    Early intervention is key to preventing relapse.
    """
    
    chunker = SmartChunker(chunk_size=700, overlap=100)
    chunks = chunker.chunk(sample_text, preserve_structure=True)
    
    print(f"\n✂️ Created {len(chunks)} chunks:\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"Chunk {i} ({len(chunk.split())} words):")
        print(f"  {chunk[:100]}...")
        print()


def demo_metadata_generation():
    """Demo 3: Show metadata generation"""
    
    print("\n" + "="*80)
    print("DEMO 3: METADATA GENERATION")
    print("="*80)
    
    sample_chunk = """
    Cognitive-behavioral therapy (CBT) is an evidence-based treatment approach that focuses
    on the relationship between thoughts, feelings, and behaviors. The core principle of CBT
    is that our thoughts influence our emotions, and by changing maladaptive thought patterns,
    we can improve emotional well-being. CBT is particularly effective for anxiety disorders,
    depression, and post-traumatic stress disorder.
    """
    
    metadata_gen = MetadataGenerator()
    metadata = metadata_gen.generate(
        sample_chunk,
        "Psychology.pdf",
        chunk_index=0,
        doc_type="psychology"
    )
    
    print("\n📋 Generated Metadata:")
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


def demo_qa_generation():
    """Demo 4: Show Q&A pair generation"""
    
    print("\n" + "="*80)
    print("DEMO 4: Q&A GENERATION")
    print("="*80)
    
    sample_chunk = """
    CBT for PTSD involves graduated exposure to trauma memories in a safe therapeutic 
    environment. Techniques include trauma focus, cognitive processing, and skills training. 
    Most patients show significant improvement within 12-16 sessions when receiving trauma-focused CBT.
    """
    
    metadata = {'topics': ['trauma', 'therapy'], 'content_type': 'treatment', 'summary': 'CBT techniques'}
    
    qa_gen = QAGenerator()
    qa_pairs = qa_gen.generate(sample_chunk, metadata)
    
    print(f"\n❓ Generated {len(qa_pairs)} Q&A Pairs:\n")
    
    for i, qa in enumerate(qa_pairs, 1):
        print(f"Q{i}: {qa['question']}")
        print(f"A{i}: {qa['answer'][:100]}...")
        print(f"    Type: {qa['type']} | Difficulty: {qa['difficulty']}")
        print()


def demo_safety_checking():
    """Demo 5: Show safety layer"""
    
    print("\n" + "="*80)
    print("DEMO 5: SAFETY LAYER")
    print("="*80)
    
    # Safe content
    safe_text = """
    Depression treatment involves a combination of psychotherapy and medication. 
    Cognitive-behavioral therapy has shown effectiveness in treating depression symptoms.
    """
    
    # Content needing disclaimer
    disclaimer_text = """
    For severe anxiety, treatment options include SSRIs and cognitive-behavioral therapy.
    Patients should consult with qualified mental health professionals.
    """
    
    safety = SafetyChecker()
    
    print("\n✅ Safe Content:")
    result1 = safety.check_text(safe_text)
    print(f"  Is safe: {result1['is_safe']}")
    print(f"  Needs disclaimer: {result1['needs_disclaimer']}")
    
    print("\n⚠️  Content needing disclaimer:")
    result2 = safety.check_text(disclaimer_text)
    print(f"  Is safe: {result2['is_safe']}")
    print(f"  Needs disclaimer: {result2['needs_disclaimer']}")
    print(f"  Disclaimer: {result2['recommended_disclaimer'][:80]}...")
    
    print("\n🆘 Available Hotlines:")
    for resource in result2['hotline_resources']:
        print(f"  {resource}")


def demo_full_pipeline():
    """Demo 6: Show complete pipeline"""
    
    print("\n" + "="*80)
    print("DEMO 6: COMPLETE PIPELINE (All 6 Components)")
    print("="*80)
    
    raw_text = """
    Page 15
    
    Clinical Depression and Treatment
    
    Depression    is    a    serious    mental    health    condition    affecting    millions    globally.
    Research indicates that cognitive-behavioral ther-
    apy (CBT) combined with appropriate medications yields
    the best outcomes. Treatment should only be delivered
    by qualified mental health profes-
    sionals.
    
    Page 16
    
    Anxiety Management
    
    Anxiety    disorders    respond    well    to    evidence-based    treatments.    Early    intervention
    improves    prognosis    significantly.
    """
    
    pipeline = TextProcessingPipeline()
    result = pipeline.process(raw_text, "Sample_Clinical_Text.txt", doc_type="psychology")
    
    print(f"\n✅ Status: {result['status']}")
    
    if result['status'] != 'success':
        print(f"Message: {result.get('message', 'Unknown error')}")
        return
    
    print(f"📊 Chunks Created: {result['statistics'].get('chunks_created', 0)}")
    print(f"❓ Q&A Pairs Generated: {result['statistics'].get('qa_pairs', 0)}")
    print(f"⏱️  Processing Time: {result['statistics'].get('processing_time', 0):.2f}s")
    
    print(f"\n🧹 Cleaning Stats:")
    clean_stats = result['statistics'].get('cleaning_stats', {})
    print(f"  • Lines removed: {clean_stats.get('lines_removed', 0)}")
    print(f"  • OCR fixes: {clean_stats.get('ocr_fixes', 0)}")
    print(f"  • Size: {clean_stats.get('input_chars', 0)} → {clean_stats.get('output_chars', 0)} chars")
    
    print(f"\n📋 First Chunk Preview:")
    if result['chunks']:
        first_chunk = result['chunks'][0]
        print(f"  Content: {first_chunk['content'][:150]}...")
        print(f"  Topics: {first_chunk['metadata']['topics']}")
        print(f"  Q&A Pairs: {len(first_chunk['qa_pairs'])}")
        print(f"  Safety: {first_chunk['safety']['is_safe']}")
    
    print(f"\n⚠️  Safety Summary:")
    safety = result.get('safety_summary', {})
    print(f"  • Total concerns: {safety.get('total_concerns', 0)}")
    print(f"  • Safe chunks: {safety.get('safe_chunks', 0)}")
    print(f"  • Chunks needing disclaimer: {safety.get('chunks_needing_disclaimer', 0)}")
    
    warnings_list = result.get('warnings', [])
    if warnings_list:
        print(f"\n⚠️  Warnings:")
        for warning in warnings_list:
            print(f"  • {warning}")


def main():
    """Run all demos"""
    
    print("\n" + "="*80)
    print("🧹 TEXT CLEANING PIPELINE - COMPLETE DEMO")
    print("="*80)
    
    try:
        demo_text_cleaner()
        demo_chunking()
        demo_metadata_generation()
        demo_qa_generation()
        demo_safety_checking()
        demo_full_pipeline()
        
        print("\n" + "="*80)
        print("✅ ALL DEMOS COMPLETE!")
        print("="*80)
        
        print("\n🚀 Next Steps:")
        print("  1. Use TextProcessingPipeline for your raw PDF data")
        print("  2. Save chunks to JSON files")
        print("  3. Ingest into ChromaDB with metadata")
        print("  4. Query with enhanced context")
        print("\nSee neuronix_cleaning_integration.py for full integration")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
