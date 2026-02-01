import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('GEMINI_API')

client = genai.Client(api_key=API_KEY)

print("Fetching available models...")
try:
    # We iterate and print safely
    for model in client.models.list():
        # Try to get the name, fallback to printing the whole object
        name = getattr(model, 'name', 'Unknown Name')
        display = getattr(model, 'display_name', '')
        
        print(f"Model ID: {name}")
        if display:
            print(f"Display:  {display}")
        print("-" * 20)

except Exception as e:
    print(f"CRITICAL ERROR: {e}")