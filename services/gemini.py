import os
import json
import google.generativeai as genai
from PIL import Image
import io
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def identify_plants_with_gemini(image_bytes: bytes):
    """
    Sends an image to Gemini and returns identified plants with details and bounding boxes.
    """
    model = genai.GenerativeModel('gemini-flash-latest')
    
    image = Image.open(io.BytesIO(image_bytes))
    
    prompt = """
    Identify all individual plants in this garden photo. 
    For each plant, provide:
    1. Common Name
    2. Plant Variety
    3. Current Condition (e.g., Healthy, Needs Water, Pest Damage)
    4. Bounding box in [ymin, xmin, ymax, xmax] format (normalized 0-1000).
    
    Return the response ONLY as a JSON list of objects:
    [
      {
        "name": "...",
        "variety": "...",
        "condition": "...",
        "box_2d": [ymin, xmin, ymax, xmax]
      }
    ]
    """
    
    try:
        response = model.generate_content([prompt, image])
        # Extract JSON from output (handling potential markdown formatting)
        content = response.text.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return []
