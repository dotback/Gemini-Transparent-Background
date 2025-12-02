from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

print("Listing available models...")
try:
    for model in client.models.list():
        print(f"Model: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Supported Actions: {model.supported_actions}")
except Exception as e:
    print(f"Error listing models: {e}")
