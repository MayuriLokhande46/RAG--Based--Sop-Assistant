import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def test_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"Testing with API Key: {api_key[:10]}...")
    
    # Try 1: v1 with gemini-1.5-flash
    print("\n--- Try 1: version='v1', model='gemini-1.5-flash' ---")
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key, version="v1")
        res = llm.invoke("Hi")
        print(f"SUCCESS: {res.content}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

    # Try 2: no version, model='gemini-1.5-flash'
    print("\n--- Try 2: no version, model='gemini-1.5-flash' ---")
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
        res = llm.invoke("Hi")
        print(f"SUCCESS: {res.content}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

    # Try 3: gemini-pro
    print("\n--- Try 3: model='gemini-pro' ---")
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=api_key)
        res = llm.invoke("Hi")
        print(f"SUCCESS: {res.content}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    test_llm()
