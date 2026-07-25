import requests
import json
import time
import threading
import os
from engine.auth import get_system_credential

gpu_mutex = threading.Lock()

def detect_loop(tokens_list: list) -> bool:
    """Infinite Word Chain State Tracker."""
    for seq_len in range(4, 21):
        if len(tokens_list) >= seq_len * 4:
            seq1 = tokens_list[-seq_len:]
            seq2 = tokens_list[-seq_len*2 : -seq_len]
            seq3 = tokens_list[-seq_len*3 : -seq_len*2]
            seq4 = tokens_list[-seq_len*4 : -seq_len*3]
            
            # Check if all four sequences are identical
            if seq1 == seq2 == seq3 == seq4:
                # Ignore if the sequence is entirely whitespace/newlines
                seq_str = "".join(seq1)
                if seq_str.strip() == "":
                    continue
                return True
    return False

def ensure_ollama_running():
    import urllib.request
    import urllib.error
    import subprocess
    try:
        urllib.request.urlopen("http://localhost:11434/", timeout=1)
    except urllib.error.URLError:
        print("[Ollama] Engine is offline. Silently auto-starting Ollama in the background...")
        if os.name == 'nt':
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3) # Give the engine a few seconds to warm up

def _generate_ollama(model: str, prompt: str, temperature: float = 0.3, format_json: bool = False) -> tuple[bool, str]:
    ensure_ollama_running()
    print(f"\n[Ollama] Loading Expert into VRAM: {model} (Temp: {temperature}, JSON: {format_json})")
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model, 
        "prompt": prompt, 
        "stream": True,
        "keep_alive": 0,
        "options": {
            "num_ctx": 32768,
            "temperature": temperature
        }
    }
    if format_json:
        payload["format"] = "json"
    
    full_response = ""
    tokens_tracker = []
    
    try:
        with gpu_mutex:
            print(f"[GPU Mutex] Lock acquired for local model: {model} (NOTE: local Ollama calls are SERIALIZED — parallel workers provide zero speedup in local mode)")
            with requests.post(url, json=payload, stream=True, timeout=300) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        full_response += token
                        tokens_tracker.append(token)
                        
                        if len(tokens_tracker) > 100:
                            tokens_tracker.pop(0)
                            
                        if detect_loop(tokens_tracker):
                            print("\n[State Hash Tracker] CRITICAL: Infinite word chain loop detected!")
                            return False, full_response
                            
                        if data.get("done", False):
                            break
                            
            print(f"\n[Ollama] Execution complete. Expert '{model}' purged from VRAM.")
            time.sleep(1) 
        print(f"[GPU Mutex] Lock released.")
        return True, full_response
        
    except Exception as e:
        print(f"[Ollama] Expert {model} failed: {e}")
        return False, f"Error: Local Ollama execution failed: {str(e)}"

def _generate_openai(model: str, prompt: str, api_key: str) -> tuple[bool, str]:
    print(f"\n[Cloud API] Routing to OpenAI/Grok endpoint: {model} (Bypassing GPU Mutex)")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return True, content
    except Exception as e:
        return False, str(e)

def _generate_groq(model: str, prompt: str, api_key: str, use_case: str = "default") -> tuple[bool, str]:
    print(f"\n[Cloud API] Routing to Groq endpoint: {model} (Bypassing GPU Mutex)")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "reasoning_effort": "high",
        "disable_tool_validation": True
    }
    
    if use_case == "resume_tailoring":
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "resume_tailoring_output",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "tailored_bullets": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "A single resume bullet point strictly following the XYZ formula based on contextual grounding."
                            }
                        }
                    },
                    "required": ["tailored_bullets"],
                    "additionalProperties": False
                }
            }
        }
    else:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return True, content
    except Exception as e:
        return False, str(e)

def _generate_openrouter(model: str, prompt: str, api_key: str) -> tuple[bool, str]:
    print(f"\n[Cloud API] Routing to OpenRouter endpoint: {model} (Bypassing GPU Mutex)")
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "SPrav Job App"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return True, content
    except Exception as e:
        return False, str(e)

def _generate_anthropic(model: str, prompt: str, api_key: str) -> tuple[bool, str]:
    print(f"\n[Cloud API] Routing to Anthropic endpoint: {model} (Bypassing GPU Mutex)")
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    payload = {
        "model": model,
        "max_tokens": 4000,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        content = response.json()["content"][0]["text"]
        return True, content
    except Exception as e:
        return False, str(e)

def _generate_gemini(model: str, prompt: str, api_key: str) -> tuple[bool, str]:
    print(f"\n[Cloud API] Routing to Gemini endpoint: {model} (Bypassing GPU Mutex)")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return True, content
    except Exception as e:
        return False, str(e)

def get_routing_config(use_case: str) -> dict:
    config_path = "config.json"
    routing = {"provider": "ollama", "model": "qwen2.5-coder:7b-instruct"}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                providers = data.get("providers", {})
                if use_case in providers:
                    return providers[use_case]
        except:
            pass
            
    # Default local mapping if no config overrides
    if use_case == "extraction":
        routing["model"] = "qwen2.5-coder:7b-instruct"
    elif use_case in ["hard_filter", "brain_retrieval"]:
        routing["model"] = "deepseek-r1:7b" # DeepSeek-R1-Distill-Qwen-7B
    elif use_case == "toxic_forensics" or use_case == "strategy_generator":
        routing["model"] = "bespoke-minicheck" # Bespoke-Minicheck-7B
    elif use_case == "resume_tailoring":
        routing["model"] = "hermes3:8b" # Hermes-3-Llama-3.1-8B
    return routing

def generate(prompt: str, use_case: str = "general") -> str:
    """
    SPrav MOE model Orchestrator.
    Dynamically routes to Local Ollama, Grok, Claude, or Gemini based on config.
    Automatically falls back to Local Ollama if a Cloud API fails.
    """
    route = get_routing_config(use_case)
    provider = route.get("provider", "ollama")
    model_name = route.get("model", "qwen2.5-coder:7b-instruct")
    
    success, result = False, ""
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            success, result = _generate_openai(model_name, prompt, api_key)
        else:
            print(f"[Agnostic MoE] Missing OpenAI key for '{use_case}'. Falling back to Ollama.")
            
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            success, result = _generate_anthropic(model_name, prompt, api_key)
        else:
            print(f"[Agnostic MoE] Missing Anthropic key for '{use_case}'. Falling back to Ollama.")
            
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            success, result = _generate_gemini(model_name, prompt, api_key)
        else:
            print(f"[Agnostic MoE] Missing Gemini key for '{use_case}'. Falling back to Ollama.")
            
    elif provider == "groq":
        api_key = get_system_credential("groq", "api_key") or os.getenv("GROQ_API_KEY")
        if api_key:
            success, result = _generate_groq(model_name, prompt, api_key, use_case)
        else:
            print(f"[Agnostic MoE] Missing Groq key for '{use_case}'. Configure it in the UI Settings. Falling back to Ollama.")
            
    elif provider == "openrouter":
        api_key = get_system_credential("openrouter", "api_key") or os.getenv("OPENROUTER_API_KEY")
        if api_key:
            success, result = _generate_openrouter(model_name, prompt, api_key)
        else:
            print(f"[Agnostic MoE] Missing OpenRouter key for '{use_case}'. Configure it in the UI Settings. Falling back to Ollama.")
            
    # Primary Local Execution or Cloud Fallback
    if not success:
        if provider != "ollama":
            print(f"[Agnostic MoE] Cloud Provider '{provider}' failed: {result}. Failing over to Local Ollama.")
            
            # Hard fallback to DeepSeek/Qwen mapping if we were trying a cloud model
            if use_case == "extraction":
                fallback_model = "qwen2.5-coder:7b-instruct"
            elif use_case in ["hard_filter", "brain_retrieval"]:
                fallback_model = "deepseek-r1:7b"
            elif use_case == "toxic_forensics" or use_case == "strategy_generator":
                fallback_model = "bespoke-minicheck"
            elif use_case == "resume_tailoring":
                fallback_model = "qwen2.5-coder:7b-instruct"
            elif use_case == "copilot":
                fallback_model = "hermes3:8b"
            else:
                fallback_model = "qwen2.5-coder:7b-instruct"
        else:
            # If Ollama is the primary provider, use the configured model_name
            fallback_model = model_name
            
        if use_case == "resume_tailoring":
            # Strict deterministic constraint for JSON formatting
            success, result = _generate_ollama(fallback_model, prompt, temperature=0.0, format_json=True)
        else:
            success, result = _generate_ollama(fallback_model, prompt, temperature=0.3)
        
        # Secondary Fallback Resolution if the local generator breaks a loop or fails JSON compliance
        if not success and "[State Hash Tracker]" in result or not success:
            if use_case == "resume_tailoring":
                secondary_model = "hermes3:8b"
                print(f"[SPrav MoE] Initiating Secondary Fallback: {secondary_model}...")
                _, fallback_result = _generate_ollama(secondary_model, prompt, temperature=0.0, format_json=True)
            else:
                print(f"[SPrav MoE] Initiating Fallback Resolution: High-Temperature {fallback_model}...")
                _, fallback_result = _generate_ollama(fallback_model, prompt, temperature=0.8)
            return fallback_result
            
    return result
