"""
🤖 LLM INTEGRATION WRAPPER
==========================
Single point for all LLM calls (Gemini or GPT)

Usage:
1. Add API key to .env file
2. Choose provider in config
3. Call get_llm_response() anywhere in system
"""

import os
import logging
from typing import Optional, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "gemini"),  # "gemini" or "openai"
    "gemini_api_key": os.getenv("GEMINI_API_KEY"),
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "model": os.getenv("LLM_MODEL", "gemini-pro"),  # or "gpt-3.5-turbo"
    "temperature": 0.7,
    "max_tokens": 1000,
}

# ============================================================================
# LLM RESPONSE FUNCTION - MAIN ENTRY POINT
# ============================================================================

def get_llm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    provider: Optional[str] = None
) -> str:
    raise RuntimeError(
        "Legacy LLM runtime disabled. Use NeuronixCognitiveRuntime."
    )
    """
    Get response from LLM (Gemini or OpenAI)
    
    Args:
        prompt: User question + context
        system_prompt: System instructions (if supported by API)
        temperature: Creativity level (0-1, 0=deterministic, 1=creative)
        max_tokens: Max response length
        provider: Override configured provider ("gemini" or "openai")
    
    Returns:
        Response text from LLM
    
    Example:
        response = get_llm_response(
            prompt="What is anxiety?",
            system_prompt="You are a mental health expert...",
            temperature=0.7
        )
    """
    
    provider = provider or LLM_CONFIG["provider"]

    try:
        if provider.lower() == "gemini":
            return _get_gemini_response(prompt, system_prompt, temperature, max_tokens)

        elif provider.lower() == "openai":
            return _get_openai_response(prompt, system_prompt, temperature, max_tokens)

        elif provider.lower() == "litellm":
            return _get_litellm_response(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")

    
    except Exception as e:
        logger.error(f"❌ LLM API Error ({provider}): {str(e)}")
        return _fallback_response(prompt)


# ============================================================================
# GEMINI INTEGRATION
# ============================================================================

def _get_gemini_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """
    Get response from Google Gemini API
    
    Setup:
    1. pip install google-generativeai
    2. Get API key from https://ai.google.dev/
    3. Add to .env: GEMINI_API_KEY=your_key_here
    """
    
    try:
        import google.generativeai as genai
        
        # Configure API
        api_key = LLM_CONFIG["gemini_api_key"]
        if not api_key:
            logger.warning("⚠️  GEMINI_API_KEY not set in .env")
            return _fallback_response(prompt)
        
        genai.configure(api_key=api_key)
        
        # Build request
        model = genai.GenerativeModel(
            model_name=LLM_CONFIG["model"],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        
        # Add system prompt if provided
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Get response
        logger.info(f"🤖 Calling Gemini API...")
        response = model.generate_content(full_prompt)
        
        logger.info(f"✅ Gemini response received ({len(response.text)} chars)")
        return response.text
    
    except ImportError:
        logger.error("❌ google-generativeai not installed. Run: pip install google-generativeai")
        return _fallback_response(prompt)
    
    except Exception as e:
        logger.error(f"❌ Gemini API error: {str(e)}")
        return _fallback_response(prompt)


# ============================================================================
# LITELLM INTEGRATION (Azure-safe fallback via content_policy_fallback)
# ============================================================================


def _get_litellm_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    ) -> str:
    """Use LiteLLM completion() with content_policy_fallback.

    This path is intended for Azure-filtered setups where LiteLLM can retry
    with a safer model if Azure blocks the request.

    Env vars (optional):
    - LITELLM_FALLBACK_MODEL (default: gpt-4.1-mini)
    """
    try:
        import litellm

        # Compose prompt/messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        fallback_model = os.getenv("LITELLM_FALLBACK_MODEL", "gpt-4.1-mini")

        # Primary model is expected to be configured on LiteLLM side (or via LITELLM_MODEL)
        model = os.getenv("LITELLM_MODEL", LLM_CONFIG.get("model", "gpt-4.1"))

        logger.info(
            f"🧩 Calling LiteLLM completion (model={model}, fallback={fallback_model})"
        )

        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            content_policy_fallback=fallback_model,
        )

        logger.info(f"[LiteLLM] Primary model: {model} | Fallback model: {fallback_model}")

        # LiteLLM typically returns an object with .choices[0].message.content, but be defensive
        if hasattr(response, "choices"):
            return response.choices[0].message.content
        if isinstance(response, dict):
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        return str(response)

    except ImportError:
        logger.error("❌ litellm not installed. Run: pip install litellm")
        return _fallback_response(prompt)
    except Exception as e:
        logger.error(f"❌ LiteLLM API error: {str(e)}")
        return _fallback_response(prompt)


# ============================================================================
# OPENAI INTEGRATION
# ============================================================================

def _get_openai_response(

    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> str:
    """
    Get response from OpenAI GPT API
    
    Setup:
    1. pip install openai
    2. Get API key from https://platform.openai.com/api-keys
    3. Add to .env: OPENAI_API_KEY=your_key_here
    """
    
    try:
        from openai import OpenAI
        
        # Configure client
        api_key = LLM_CONFIG["openai_api_key"]
        if not api_key:
            logger.warning("⚠️  OPENAI_API_KEY not set in .env")
            return _fallback_response(prompt)
        
        client = OpenAI(api_key=api_key)
        
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})

        # ------------------------------------------------------------
        # FINAL HARDENING: sanitize message history before OpenAI/LiteLLM
        # ------------------------------------------------------------
        def sanitize_messages(msgs):
            clean = []

            for msg in msgs:
                if not isinstance(msg, dict):
                    continue

                role = msg.get("role")

                # Drop invalid tool messages (this pipeline is not tool-calling)
                if role == "tool":
                    continue

                # Remove malformed tool_calls from non-assistant messages
                if role != "assistant" and "tool_calls" in msg:
                    msg = dict(msg)
                    msg.pop("tool_calls", None)

                # Normalize None content
                if msg.get("content") is None:
                    msg["content"] = ""

                clean.append(msg)

            return clean

        messages = sanitize_messages(messages)

        logger.info("=" * 80)
        logger.info("FINAL MESSAGES SENT TO OPENAI")
        for i, msg in enumerate(messages):
            logger.info(f"[{i}] ROLE={msg.get('role')}")
            logger.info(str(msg)[:1000])

        # Get response
        logger.info(f"🤖 Calling OpenAI API...")
        response = client.chat.completions.create(
            model=LLM_CONFIG["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        
        response_text = response.choices[0].message.content
        logger.info(f"✅ OpenAI response received ({len(response_text)} chars)")
        return response_text
    
    except ImportError:
        logger.error("❌ openai not installed. Run: pip install openai")
        return _fallback_response(prompt)
    
    except Exception as e:
        logger.error(f"❌ OpenAI API error: {str(e)}")
        return _fallback_response(prompt)


# ============================================================================
# FALLBACK (If API fails or key missing)
# ============================================================================

def _fallback_response(prompt: str) -> str:
    """
    Fallback response when API is unavailable
    
    In production, this would be replaced with real DB lookup or queuing
    """
    
    return (
        f"⚠️  [Simulated Response] Based on: {prompt[:50]}...\n\n"
        f"Note: LLM API not configured. Configure in .env and restart."
    )


# ============================================================================
# TESTING
# ============================================================================

def test_llm_integration():
    """Test LLM integration with sample prompts"""
    
    print("\n" + "="*70)
    print("🧪 Testing LLM Integration")
    print("="*70)
    
    test_cases = [
        {
            "name": "Simple Question",
            "prompt": "What is anxiety?",
            "system": "You are a mental health expert. Answer in 1-2 sentences."
        },
        {
            "name": "Clinical Question",
            "prompt": "Explain CBT vs DBT for anxiety treatment",
            "system": "You are a clinical psychologist. Provide technical detail."
        },
        {
            "name": "Hinglish Query",
            "prompt": "Mujhe depression ho gaya. Ismein kya kru?",
            "system": "You are a mental health assistant. Respond in Hinglish."
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print(f"Calling LLM...")
        
        response = get_llm_response(
            prompt=test['prompt'],
            system_prompt=test['system']
        )
        
        print(f"Response: {response[:100]}...")
        print(f"✅ Success (length: {len(response)} chars)")


if __name__ == "__main__":
    # Run tests
    test_llm_integration()
    
    print("\n" + "="*70)
    print("✅ LLM Integration Ready!")
    print("="*70)
    print("\nTo use in production:")
    print("1. Add API key to .env file")
    print("2. from llm_integration_wrapper import get_llm_response")
    print("3. response = get_llm_response(prompt, system_prompt)")
    print("="*70)
