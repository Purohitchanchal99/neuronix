#!/usr/bin/env python3
"""
Test script for NEURONIX Backend API
Verifies the API is working without needing frontend
"""

import asyncio
import httpx
import json
from typing import Dict

BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


async def test_health() -> bool:
    """Test health endpoint"""
    print(f"\n{YELLOW}[1/5] Testing health endpoint...{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ API is running{RESET}")
            print(f"   Status: {data['status']}")
            print(f"   RAG System: {data['rag_system']}")
            print(f"   DB Ready: {data['db_ready']}")
            return True
        else:
            print(f"{RED}❌ Health check failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Connection error: {e}{RESET}")
        print(f"   Make sure backend is running: python backend_api_template.py")
        return False


async def test_status() -> bool:
    """Test detailed status endpoint"""
    print(f"\n{YELLOW}[2/5] Testing status endpoint...{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/api/status", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Status retrieved{RESET}")
            print(f"   Ready: {data['ready']}")
            print(f"   Documents in DB: {data.get('documents', 0):,}")
            if data['ready']:
                return True
            else:
                print(f"{YELLOW}⚠️  Database not ready. Run: python neuronix_query.py{RESET}")
                return False
        else:
            print(f"{RED}❌ Status check failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


async def test_chat_basic() -> bool:
    """Test basic chat endpoint"""
    print(f"\n{YELLOW}[3/5] Testing chat endpoint (basic question)...{RESET}")
    try:
        payload = {
            "message": "What is depression?",
            "country": "India",
            "chunks": 6
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/chat",
                json=payload,
                timeout=TIMEOUT
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Chat response received{RESET}")
            print(f"   Response length: {len(data['response'])} chars")
            print(f"   Sources: {len(data.get('sources', []))} found")
            print(f"   Suggestions: {len(data.get('suggestions', []))} generated")
            print(f"\n   Sample response (first 200 chars):")
            print(f"   {data['response'][:200]}...")
            return True
        else:
            print(f"{RED}❌ Chat failed: {response.status_code}{RESET}")
            print(f"   {response.text}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


async def test_crisis_detection() -> bool:
    """Test crisis detection"""
    print(f"\n{YELLOW}[4/5] Testing crisis detection...{RESET}")
    try:
        payload = {
            "message": "I want to kill myself",
            "country": "India",
            "chunks": 6
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/api/chat",
                json=payload,
                timeout=TIMEOUT
            )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('is_crisis'):
                print(f"{GREEN}✅ Crisis detection working{RESET}")
                print(f"   Crisis flag: {data['is_crisis']}")
                if data.get('crisis_resources'):
                    resources = data['crisis_resources']
                    print(f"   Hotline: {resources.get('hotline')}")
                    print(f"   Resources: {resources.get('resources')}")
                return True
            else:
                print(f"{YELLOW}⚠️  Crisis not detected (unexpected){RESET}")
                return False
        else:
            print(f"{RED}❌ Crisis test failed: {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


async def test_sessions() -> bool:
    """Test session management"""
    print(f"\n{YELLOW}[5/5] Testing session management...{RESET}")
    try:
        async with httpx.AsyncClient() as client:
            # Get existing sessions
            response = await client.get(f"{BASE_URL}/api/sessions", timeout=TIMEOUT)
            
            if response.status_code == 200:
                sessions_data = response.json()
                print(f"{GREEN}✅ Session retrieval working{RESET}")
                print(f"   Existing sessions: {sessions_data['count']}")
                
                # Create new session
                response = await client.post(
                    f"{BASE_URL}/api/sessions",
                    json={"messages": [], "metadata": {"test": True}},
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    session = response.json()
                    print(f"   Created session: {session['id']}")
                    return True
                else:
                    print(f"{RED}❌ Session creation failed: {response.status_code}{RESET}")
                    return False
            else:
                print(f"{RED}❌ Session retrieval failed: {response.status_code}{RESET}")
                return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False


async def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 NEURONIX Backend API Tests")
    print("=" * 80)
    
    results = []
    
    # Run tests
    results.append(("Health Check", await test_health()))
    results.append(("Status Check", await test_status()))
    results.append(("Chat Endpoint", await test_chat_basic()))
    results.append(("Crisis Detection", await test_crisis_detection()))
    results.append(("Session Management", await test_sessions()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✅ PASSED{RESET}" if result else f"{RED}❌ FAILED{RESET}"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}🎉 All tests passed! API is ready.{RESET}")
        print("\nNext steps:")
        print("1. Start frontend: cd frontend && npm run dev")
        print("2. Open http://localhost:3000")
        print("3. Start chatting! 💬")
    else:
        print(f"\n{RED}⚠️  Some tests failed. Check output above.{RESET}")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
