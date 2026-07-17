import os
from google import genai

api_key = "AIzaSyA3UzN9eWGIFq3_7bqMZ_rOAdY3j7NRalE"
client = genai.Client(api_key=api_key)

models_to_test = ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-flash-latest"]
for model in models_to_test:
    try:
        response = client.models.generate_content(
            model=model,
            contents="Hello",
        )
        print(f"Model {model} SUCCESS: {response.text}")
    except Exception as e:
        print(f"Model {model} FAILED: {e}")
