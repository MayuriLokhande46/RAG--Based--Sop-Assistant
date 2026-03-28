import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
os.environ["GOOGLE_API_VERSION"] = "v1"

def test_llm_env():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"Testing with GOOGLE_API_VERSION='v1' and model='gemini-1.5-flash-latest'...")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest", 
            google_api_key=api_key
        )
        res = llm.invoke("Hi")
        print(f"SUCCESS: {res.content}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    test_llm_env()
