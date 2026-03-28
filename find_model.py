import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def find_working_model():
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    print("Listing all available models for generation...")
    models_to_try = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models_to_try.append(m.name)
                print(f"Found: {m.name}")
    except Exception as e:
        print(f"List models failed: {str(e)}")
        return

    print("\nStarting brute-force connectivity check...")
    for model_name in models_to_try:
        short_name = model_name.replace("models/", "")
        print(f"Testing model: {model_name} (Short: {short_name})...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Hi")
            print(f"SUCCESS with {model_name}: {response.text[:20]}...")
            return model_name
        except Exception as e:
            print(f"FAILED {model_name}: {str(e)[:100]}")
            
    print("\nNo models worked.")
    return None

if __name__ == "__main__":
    find_working_model()
