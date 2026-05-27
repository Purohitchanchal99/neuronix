# -*- coding: utf-8 -*-
"""
NEURONIX STREAMLIT APP
======================
Browser-based chat interface for Neuronix clinical AI

Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os
import logging
import time
import uuid
from pathlib import Path
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.chat_engine import NeuronixChatEngine
from backend.session_manager import SessionManager

# ================================================================
# PAGE CONFIGURATION
# ================================================================
st.set_page_config(
    page_title="Neuronix - Clinical AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================================================================
# CSS STYLING - MINIMAL
# ================================================================
st.markdown("""
    <style>
    .stChatMessage {
        border-radius: 8px;
        padding: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ================================================================
# INITIALIZE SESSION STATE
# ================================================================
if "chat_engine" not in st.session_state:
    try:
        st.session_state.chat_engine = NeuronixChatEngine()
        st.session_state.db_status = st.session_state.chat_engine.get_db_status()
    except ValueError as e:
        st.error(f"❌ Error: {e}\n\nPlease set GOOGLE_API_KEY environment variable")
        st.stop()

if "session_manager" not in st.session_state:
    try:
        st.session_state.session_manager = SessionManager()
    except Exception as e:
        st.error(f"❌ Database Error: {e}")
        st.stop()

# Initialize other session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_query" not in st.session_state:
    st.session_state.last_query = ""

if "conversation_mood_trend" not in st.session_state:
    st.session_state.conversation_mood_trend = {}

if "user_id" not in st.session_state:
    # Create new user
    st.session_state.user_id = st.session_state.session_manager.create_user(
        username="WebUser",
        country="India"
    )

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "conversation_mood_trend" not in st.session_state:
    st.session_state.conversation_mood_trend = {}

if "last_query" not in st.session_state:
    st.session_state.last_query = None

# ================================================================
# SIDEBAR - MINIMAL
# ================================================================
with st.sidebar:
    st.header("🧠 Neuronix")
    
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    
    if st.button("🆕 New Session", use_container_width=True):
        st.session_state.user_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    # Debug Mode Toggle
    debug_mode = st.checkbox("🔧 Debug Mode", value=False)
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = debug_mode
    else:
        st.session_state.debug_mode = debug_mode
    
    if debug_mode:
        st.info("🐛 Debug mode enabled - Raw retrieval results will be shown")
        if st.button("📊 Show DB Status"):
            st.write("Vector DB Status:")
            try:
                db_info = st.session_state.chat_engine.get_db_status()
                st.code(db_info)
            except Exception as e:
                st.error(f"Error getting DB status: {e}")
    
    st.divider()
    st.caption("💡 Tip: Type your concern in plain language")

# ================================================================
# MAIN CHAT INTERFACE - CLEAN & SIMPLE
# ================================================================

st.title("🧠 Neuronix")
st.caption("Your AI mental health companion | Everything stays private")

# Display chat history
if st.session_state.chat_history:
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])
        else:  # assistant
            with st.chat_message("assistant", avatar="🧠"):
                st.markdown(message["content"])
else:
    st.info("👋 Share what's on your mind. I'm here to listen and help.")

# Input area
user_input = st.chat_input(
    "Type your concern...",
    key="user_input"
)

if user_input:
    # CHECK: Make sure we're only processing NEW messages (not re-runs of old ones)
    if st.session_state.last_query == user_input:
        # Skip if this is the same query as before (prevents double-processing)
        pass
    else:
        # NEW message detected - process it
        st.session_state.last_query = user_input
        
        # Add user message to chat history (FIRST)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Show user message immediately
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        
        # Generate response (using ONLY the latest message)
        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("🤔 Neuronix is thinking..."):
                try:
                    # Get response from chat engine (only current query, not history)
                    response = st.session_state.chat_engine.chat(user_input)
                    
                    # Analyze tone
                    tone = st.session_state.chat_engine.tone_analyzer.analyze_tone(user_input)
                    
                    # Store in database with retry logic for locks
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            st.session_state.session_manager.add_message(
                                st.session_state.user_id,
                                user_input,
                                response,
                                detected_mood=tone
                            )
                            break  # Success, exit retry loop
                        except Exception as e:
                            if "locked" in str(e).lower() and attempt < max_retries - 1:
                                time.sleep(0.5)  # Wait and retry
                                continue
                            else:
                                logger.warning(f"Failed to store message (attempt {attempt+1}): {e}")
                                break  # Give up or final attempt
                    
                    # Display response
                    st.markdown(response)
                    
                    # Show debug info if enabled
                    if st.session_state.debug_mode:
                        with st.expander("🔍 Debug Info"):
                            try:
                                # Try to retrieve docs for this query
                                from langchain_community.vectorstores import Chroma
                                retrieval_docs = st.session_state.chat_engine.vector_store.similarity_search(
                                    user_input, k=3
                                )
                                
                                st.write(f"**Retrieval Results:** {len(retrieval_docs)} documents found")
                                if retrieval_docs:
                                    for i, doc in enumerate(retrieval_docs, 1):
                                        st.write(f"**Doc {i}:**")
                                        st.code(doc.page_content[:300] + "...")
                                else:
                                    st.warning("⚠️ No documents retrieved - Vector DB may be empty!")
                                
                                # Show query classification
                                query_type = st.session_state.chat_engine._classify_query_type(user_input)
                                st.write(f"**Query Type:** {query_type}")
                                
                            except Exception as e:
                                st.error(f"Debug info error: {e}")
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                    
                    # Update mood trend (internal tracking)
                    if tone != "neutral":
                        if tone not in st.session_state.conversation_mood_trend:
                            st.session_state.conversation_mood_trend[tone] = 0
                        st.session_state.conversation_mood_trend[tone] += 1
                    
                    st.rerun()  # Refresh to scroll to latest message
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    logger.error(f"Chat error: {e}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")

# ================================================================
# FOOTER
# ================================================================
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.85rem;">
        <p>🏥 Neuronix Clinical Psychology AI | Day 4: Memory & Empathy</p>
        <p>⚠️ Disclaimer: This is an educational tool. Always seek professional medical advice for serious concerns.</p>
        <p>Build with ❤️ for mental health awareness | © 2026 Neuronix Project</p>
    </div>
""", unsafe_allow_html=True)
