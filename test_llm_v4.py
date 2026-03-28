import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def test_llm_new():
    api_key = os.getenv("GOOGLE_API_KEY")
    print(f"Testing with langchain-google-genai 4.2.1 and model='gemini-1.5-flash'...")
    
    try:
        # v4.2.1 uses google-genai SDK, no 'version' argument in constructor
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=api_key
        )
        res = llm.invoke("Hi")
        print(f"SUCCESS: {res.content}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    test_llm_new()
