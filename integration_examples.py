"""
📋 NEURONIX INTEGRATION EXAMPLES & QUICKSTART
============================================
Practical, copy-paste examples for using the complete post-ingestion system
"""

import json
from datetime import datetime
from integration_system import NeuronixPostIngestionSystem


# ============================================================================
# EXAMPLE 1: BASIC INGESTION WORKFLOW
# ============================================================================

def example_1_basic_ingestion():
    """
    Simplest ingestion workflow:
    1. Initialize system
    2. Ingest PDF
    3. Validate
    4. Get status
    """
    
    print("\n" + "="*70)
    print("EXAMPLE 1: BASIC INGESTION WORKFLOW")
    print("="*70)
    
    # Initialize
    system = NeuronixPostIngestionSystem()
    
    # Ingest DSM-5 PDF
    result = system.ingest_pdf_with_metadata(
        pdf_path="resources/dsm5_chapter2.pdf",
        batch_id="batch_001",
        domain_tags=["diagnostic", "psychiatric"],
        chapter=2,
        section="Depressive Disorders"
    )
    
    print(f"\n✅ Ingestion Result:")
    print(json.dumps(result, indent=2))
    
    # Get status
    status = system.get_system_status()
    print(f"\n📊 System Status:")
    print(json.dumps(status, indent=2))
    
    # Validate batch
    batch_info = {
        "batch_id": "batch_001",
        "expected_chunks": 3,
        "actual_chunks": result.get("chunks_created", 0)
    }
    validation = system.validate_batch_checkpoint(batch_info)
    print(f"\n✅ Validation Result:")
    print(json.dumps(validation, indent=2))


# ============================================================================
# EXAMPLE 2: QUERY WITH PRECISION FILTERING
# ============================================================================

def example_2_precision_query():
    """
    Execute query with full precision layer:
    1. Clean query (semantic + Hinglish)
    2. Filter by metadata
    3. Calculate similarity
    4. Route through hybrid system
    """
    
    print("\n" + "="*70)
    print("EXAMPLE 2: PRECISION QUERY WITH FILTERING")
    print("="*70)
    
    system = NeuronixPostIngestionSystem()
    
    # Query Examples in Different Styles
    queries = [
        "What is anxiety?",
        "Anxiety kya hai?",  # Hinglish
        "Anxieyt symptoms",  # Misspelled
        "soch ki bimari ka ilaj kya hai",  # Hindi for "what's the treatment for thought disorder"
    ]
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 50)
        
        result = system.execute_precision_query(
            query=query,
            domain_filters=["psychiatric", "diagnostic"],
            user_difficulty="intermediate"
        )
        
        print(f"✅ Cleaned Query: {result['cleaned_query']}")
        print(f"📊 Results Found: {result['metadata']['results_count']}")
        print(f"🤖 Model Used: {result['model_used']}")
        print(f"⚡ Routing Decision: {result['routing_decision']['decision_reason']}")
        
        if result.get('response'):
            print(f"💬 Response Preview: {result['response'][:200]}...")


# ============================================================================
# EXAMPLE 3: BATCH INGESTION WITH MONITORING
# ============================================================================

def example_3_batch_ingestion_with_monitoring():
    """
    Ingest multiple PDFs with real-time monitoring
    Demonstrates checkpoint validation at batch level
    """
    
    print("\n" + "="*70)
    print("EXAMPLE 3: BATCH INGESTION WITH MONITORING")
    print("="*70)
    
    system = NeuronixPostIngestionSystem()
    
    # Start monitoring
    print("\n⏱️  Starting batch monitoring (periodic updates every 2 minutes)...")
    system.monitor.start_periodic_monitoring(interval_minutes=2)
    
    # Batch PDF list
    pdfs = [
        {
            "path": "dsm5_chapter2.pdf",
            "domain_tags": ["diagnostic", "psychiatric"],
            "chapter": 2,
            "section": "Depressive Disorders"
        },
        {
            "path": "dsm5_chapter5.pdf",
            "domain_tags": ["diagnostic", "anxiety"],
            "chapter": 5,
            "section": "Anxiety Disorders"
        },
        {
            "path": "icd11_mental_health.pdf",
            "domain_tags": ["diagnostic", "icd11"],
            "chapter": 1,
            "section": "Mental Health Categories"
        }
    ]
    
    batch_results = []
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    print(f"\n🎯 Batch ID: {batch_id}")
    print(f"📊 Total PDFs: {len(pdfs)}")
    print("-" * 50)
    
    for i, pdf_config in enumerate(pdfs, 1):
        print(f"\n[{i}/{len(pdfs)}] Ingesting: {pdf_config['path']}")
        
        result = system.ingest_pdf_with_metadata(
            pdf_path=pdf_config['path'],
            batch_id=batch_id,
            domain_tags=pdf_config['domain_tags'],
            chapter=pdf_config['chapter'],
            section=pdf_config['section']
        )
        
        batch_results.append(result)
        print(f"✅ Chunks Created: {result.get('chunks_created', 0)}")
    
    # Validate entire batch
    print("\n" + "-" * 50)
    print("🔍 BATCH VALIDATION")
    print("-" * 50)
    
    total_chunks = sum(r.get('chunks_created', 0) for r in batch_results)
    batch_validation = system.validate_batch_checkpoint({
        "batch_id": batch_id,
        "expected_chunks": total_chunks,
        "actual_chunks": total_chunks,
        "pdf_count": len(pdfs)
    })
    
    print(f"✅ Validation Status: {batch_validation['status']}")
    
    # Get monitoring report
    print("\n" + "-" * 50)
    print("📊 MONITORING REPORT")
    print("-" * 50)
    
    status = system.get_system_status()
    print(f"Active Ingestions: {status['ingestion_state']['chunks_created']}")
    print(f"Embeddings Stored: {status['ingestion_state']['embeddings_stored']}")
    
    # Stop monitoring
    system.monitor.stop_monitoring()
    print("\n✅ Monitoring stopped")


# ============================================================================
# EXAMPLE 4: SEMANTIC CLEANUP DEMONSTRATION
# ============================================================================

def example_4_semantic_cleanup():
    """
    Demonstrate semantic normalization:
    1. Hinglish normalization
    2. Fuzzy matching (typo correction)
    3. Intent mapping
    """
    
    print("\n" + "="*70)
    print("EXAMPLE 4: SEMANTIC CLEANUP DEMONSTRATION")
    print("="*70)
    
    system = NeuronixPostIngestionSystem()
    
    # Various text samples
    samples = [
        "Depression is a mental disorder",
        "Dimag ki bimari nahi hai ye haqeeqat hai",  # "It's not a mind disease, it's a fact" in Hinglish
        "Anxeity symptoms include panic atacks",  # Misspelled
        "mujhe har samay ghabara hota hai",  # "I get scared all the time" in Hindi
        "ADHD ka matalb kya hota h",  # "What does ADHD mean" in Hindi
    ]
    
    print("\n🧹 SEMANTIC CLEANUP RESULTS:")
    print("-" * 70)
    
    cleaned = system.clean_and_normalize_chunks(samples, "example_batch")
    
    for i, result in enumerate(cleaned, 1):
        print(f"\n[{i}] Original: {result['original']}")
        print(f"    Cleaned: {result['cleaned']}")
        print(f"    Intent Mapped: {result['intent_mapped']}")
        print(f"    Quality Score: {result['cleaning_score']:.2f}")


# ============================================================================
# EXAMPLE 5: ERROR HANDLING & RECOVERY
# ============================================================================

def example_5_error_handling():
    """
    Demonstrate error handling and recovery:
    1. Invalid inputs
    2. API failures with fallback
    3. Quota exhaustion
    """
    
    print("\n" + "="*70)
    print("EXAMPLE 5: ERROR HANDLING & RECOVERY")
    print("="*70)
    
    system = NeuronixPostIngestionSystem()
    
    print("\n1️⃣ HANDLING MISSING FILES")
    print("-" * 50)
    try:
        result = system.ingest_pdf_with_metadata(
            pdf_path="nonexistent.pdf",
            batch_id="batch_error_1",
            domain_tags=["test"],
            chapter=1,
            section="Test"
        )
        print(f"Result: {result['status']}")
        if result['status'] == 'failed':
            print(f"Error: {result['error']}")
    except Exception as e:
        print(f"Exception caught: {e}")
    
    print("\n2️⃣ CHECKING QUOTA STATUS")
    print("-" * 50)
    quota_status = system.quota_manager.get_quota_status()
    print(f"Daily Limit: {quota_status['daily_limit']}")
    print(f"Used Today: {quota_status['used_today']}")
    print(f"Remaining: {quota_status['remaining']}")
    print(f"Status: {'🟢 Available' if quota_status['available'] else '🔴 Exhausted'}")
    
    print("\n3️⃣ CHECKING ROUTING STATISTICS")
    print("-" * 50)
    stats = system.router.get_routing_stats()
    print(f"Total Requests: {stats['total_requests']}")
    print(f"Gemini Used: {stats['gemini_requests']}")
    print(f"HuggingFace Fallback: {stats['huggingface_requests']}")
    print(f"Local Emergency: {stats['local_requests']}")


# ============================================================================
# EXAMPLE 6: COMPLETE WORKFLOW (END-TO-END)
# ============================================================================

def example_6_complete_workflow():
    """
    Complete workflow from ingestion to query
    """
    
    print("\n" + "="*70)
    print("EXAMPLE 6: COMPLETE END-TO-END WORKFLOW")
    print("="*70)
    
    system = NeuronixPostIngestionSystem()
    
    # Step 1: Ingest
    print("\n📌 STEP 1: PDF INGESTION WITH METADATA")
    print("-" * 50)
    ingest_result = system.ingest_pdf_with_metadata(
        pdf_path="clinical_resource.pdf",
        batch_id="workflow_001",
        domain_tags=["diagnostic", "psychiatric", "clinical"],
        chapter=3,
        section="Clinical Assessment"
    )
    print(f"✅ Ingestion: {ingest_result['status']}")
    print(f"📊 Chunks: {ingest_result.get('chunks_created', 0)}")
    
    # Step 2: Cleanup
    print("\n📌 STEP 2: SEMANTIC CLEANUP")
    print("-" * 50)
    test_content = [
        "Patient has insomnyia and anxeity",
        "Rogi ko neend nahi aati aur ghabara rahta hai"
    ]
    cleanup_result = system.clean_and_normalize_chunks(test_content, "workflow_001")
    print(f"✅ Cleaned {len(cleanup_result)} items")
    
    # Step 3: Validate
    print("\n📌 STEP 3: CHECKPOINT VALIDATION")
    print("-" * 50)
    validation = system.validate_batch_checkpoint({
        "batch_id": "workflow_001",
        "expected_chunks": 3,
        "actual_chunks": 3
    })
    print(f"✅ Validation: {validation['status']}")
    
    # Step 4: Execute Query
    print("\n📌 STEP 4: PRECISION QUERY")
    print("-" * 50)
    query_result = system.execute_precision_query(
        query="What are the symptoms of anxiety?",
        domain_filters=["psychiatric", "diagnostic"],
        user_difficulty="beginner"
    )
    print(f"✅ Query: '{query_result['original_query']}'")
    print(f"📊 Results: {query_result['metadata']['results_count']}")
    print(f"🤖 Model: {query_result['model_used']}")
    
    # Step 5: Generate Report
    print("\n📌 STEP 5: GENERATE SYSTEM REPORT")
    print("-" * 50)
    report = system.save_full_report()
    print(f"✅ Report saved: {report['timestamp']}")
    print(f"📁 Logs: {report['logs_file']}")
    print(f"📁 Validation: {report['validation_file']}")
    
    # Step 6: Final Status
    print("\n📌 STEP 6: FINAL SYSTEM STATUS")
    print("-" * 50)
    status = system.get_system_status()
    print(f"✅ Chunks Created: {status['ingestion_state']['chunks_created']}")
    print(f"✅ Routing Decisions: {status['routing_stats']['total_requests']}")


# ============================================================================
# QUICK START GUIDANCE
# ============================================================================

QUICK_START_GUIDE = """
🚀 NEURONIX POST-INGESTION QUICK START
=====================================

📖 BASIC USAGE:

    from integration_system import NeuronixPostIngestionSystem
    
    # 1. Initialize
    system = NeuronixPostIngestionSystem()
    
    # 2. Ingest PDF
    result = system.ingest_pdf_with_metadata(
        pdf_path="your_pdf.pdf",
        batch_id="batch_id",
        domain_tags=["tag1", "tag2"],
        chapter=1,
        section="Section Name"
    )
    
    # 3. Query
    result = system.execute_precision_query(
        query="your query",
        domain_filters=["tag1"],
        user_difficulty="beginner|intermediate|advanced"
    )


⚡ FEATURES:

    ✅ Automatic metadata attachment (DSM-5, ICD-11 support)
    ✅ Hinglish normalization & fuzzy matching
    ✅ Batch checkpoint validation with detailed logging
    ✅ Dual-filter query precision (metadata + embeddings)
    ✅ Real-time monitoring (2-minute periodic updates)
    ✅ Hybrid API routing (Gemini → HuggingFace → Local)


📊 MONITORING:

    system.monitor.start_periodic_monitoring(interval_minutes=2)
    status = system.get_system_status()
    report = system.save_full_report()


🔧 CONFIGURATION:

    domain_tags = ["diagnostic", "psychiatric", "therapeutic"]
    user_difficulties = ["beginner", "intermediate", "advanced"]
    models = ["gemini-1.5-pro", "all-MiniLM-L6-v2"]
"""


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    
    print(QUICK_START_GUIDE)
    
    # Run examples
    print("\n\n" + "="*70)
    print("RUNNING INTEGRATION EXAMPLES")
    print("="*70)
    
    try:
        print("\n✅ Example 1: Basic Ingestion")
        example_1_basic_ingestion()
        
        print("\n✅ Example 2: Precision Query")
        example_2_precision_query()
        
        print("\n✅ Example 3: Batch Ingestion with Monitoring")
        example_3_batch_ingestion_with_monitoring()
        
        print("\n✅ Example 4: Semantic Cleanup")
        example_4_semantic_cleanup()
        
        print("\n✅ Example 5: Error Handling")
        example_5_error_handling()
        
        print("\n✅ Example 6: Complete Workflow")
        example_6_complete_workflow()
        
    except Exception as e:
        print(f"\n❌ Error in examples: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ ALL EXAMPLES COMPLETED")
    print("="*70)
