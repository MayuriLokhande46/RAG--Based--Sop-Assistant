import os
from google import genai
from google.genai import errors
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

def list_models():
    client = genai.Client(api_key=api_key)
    print("--- Listing Models ---")
    try:
        for model in client.models.list():
            print(f"Name: {model.name}, Display Name: {model.display_name}, Supported: {model.supported_actions}")
    except Exception as e:
        print(f"Error listing models: {e}")

def test_model(model_name):
    print(f"\n--- Testing Model: {model_name} ---")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents="Hello, are you working?"
        )
        print(f"Success! Response: {response.text}")
    except errors.ClientError as e:
        print(f"ClientError ({model_name}): {e}")
    except Exception as e:
        print(f"Error ({model_name}): {e}")

if __name__ == "__main__":
    list_models()
    test_model("gemini-1.5-flash")
    test_model("gemini-1.5-flash-latest")
    test_model("gemini-2.0-flash")
