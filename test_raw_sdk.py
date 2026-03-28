import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def test_raw_sdk():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print("Testing with raw google-genai SDK...")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hi"
        )
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    test_raw_sdk()
