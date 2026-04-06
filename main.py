import os
import sys
from dotenv import load_dotenv

# Thêm path để có thể chạy trực tiếp từ thư mục gốc
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.tools.movie_tools import get_movie_tools
from src.agent.agent import ReActAgent

def get_provider():
    load_dotenv()
    provider_type = os.getenv("DEFAULT_PROVIDER", "local").lower()
    
    if provider_type == "openai":
        from src.core.openai_provider import OpenAIProvider
        return OpenAIProvider()
    elif provider_type == "gemini":
        from src.core.gemini_provider import GeminiProvider
        return GeminiProvider()
    elif provider_type == "local":
        from src.core.local_provider import LocalProvider
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=model_path)
    else:
        raise ValueError(f"Unknown provider: {provider_type}")

def run_movie_agent():
    print("Loading dotenv and Initializing LLM Provider...")
    try:
        llm = get_provider()
        print(f"Using Provider: {llm.__class__.__name__}")
    except Exception as e:
        print(f"Failed to load provider: {e}")
        return
    
    prompt = "I'm looking for a good action movie from 2024. Can you find some and give me details of the best one?"
    
    print("\n" + "="*80)
    print("🤖 CHATBOT BASELINE (No Tools)")
    print("="*80)
    print(f"User: {prompt}\n")
    try:
        response_dict = llm.generate(prompt)
        print(f"Chatbot:\n{response_dict.get('content', '')}")
    except Exception as e:
        print(f"Chatbot failed: {e}")
        
    print("\n" + "="*80)
    print("🕵️‍♂️ REACT AGENT (With Movie Tools)")
    print("="*80)
    
    tools = get_movie_tools()
    agent = ReActAgent(llm=llm, tools=tools, max_steps=10)
    
    print(f"User: {prompt}\n")
    try:
        final_answer = agent.run(prompt)
        print(f"\nFinal Agent Answer: {final_answer}")
    except Exception as e:
        print(f"\nAgent execution failed: {e}")

if __name__ == "__main__":
    run_movie_agent()
