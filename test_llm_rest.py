import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def test_llm_rest():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"Testing with REST transport and version='v1'...")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=api_key, 
            model_kwargs={"version": "v1", "transport": "rest"}
        )
        res = llm.invoke("Hi")
        print(f"SUCCESS: {res.content}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    test_llm_rest()
