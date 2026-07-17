import os
from google import genai
from dotenv import load_dotenv

# Try to find and load the key env
load_dotenv("/Users/ritika/AgentSmith/.env")

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key: {api_key[:10]}...")

client = genai.Client(api_key=api_key)

try:
    for m in client.models.list():
        print(f"- {m.name}")
    
    print("\nTesting gemini-flash-lite-latest...")
    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents="Hello, say test",
    )
    print("Response:", response.text)
except Exception as e:
    print(f"Error: {e}")
