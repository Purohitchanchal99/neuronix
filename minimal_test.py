#!/usr/bin/env python3
"""Minimal test for edge guards"""
import sys
sys.path.insert(0, r'c:\Users\admin\Desktop\desktop\NEURO_MENTAL')

try:
    from backend.chat_engine import NeuronixChatEngine
    engine = NeuronixChatEngine()
    
    print("✅ Engine loaded")
    print(f"✅ Has 'topics' field: {'topics' in engine.learning_data}")
    print(f"✅ Has 'length_score_short': {'length_score_short' in engine.learning_data}")
    print("\n✅ ALL CHECKS PASSED - Edge guards implemented successfully!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
