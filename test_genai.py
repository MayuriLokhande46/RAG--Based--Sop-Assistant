import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def test_genai():
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    
    print("Listing models...")
    try:
        for m in client.models.list():
            if 'generateContent' in m.supported_generation_methods:
                print(f"MODEL: {m.name}")
    except Exception as e:
        print(f"LIST MODELS FAILED: {str(e)}")

    print("\nAttempting generation with gemini-1.5-flash...")
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hi"
        )
        print(f"SUCCESS: {response.text}")
    except Exception as e:
        print(f"GENERATION FAILED: {str(e)}")

if __name__ == "__main__":
    test_genai()
