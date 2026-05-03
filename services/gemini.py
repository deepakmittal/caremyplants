import os
import json
import google.generativeai as genai
from PIL import Image
import io
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

def _call_gemini(contents: list) -> dict:
    """Helper to call Gemini and parse JSON response."""
    model = genai.GenerativeModel('gemini-2.5-flash')
    try:
        response = model.generate_content(contents)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return {}

def identify_plants_with_gemini(image_list: List[bytes]):
    """
    Identifies plants and suggests a garden name.
    """
    valid_images = []
    for img_bytes in image_list:
        try:
            valid_images.append(Image.open(io.BytesIO(img_bytes)))
        except:
            continue
            
    if not valid_images:
        return [], ""

    prompt = """
    Exhaustively identify EVERY individual plant visible in these garden photos. 
    Include plants in the foreground, background, and those partially obscured. 

    For each plant provide:
    1. Common Name and Variety.
    2. Condition: Small comma separated list (e.g., "vibrant, healthy").
    3. photo_index: 0-based index of the photo.
    4. box_2d: bounding box [ymin, xmin, ymax, xmax] (0-1000).
    5. confidence: a float between 0 and 1 representing your confidence in this identification.

    Return ONLY a JSON object:
    {
      "suggested_garden_name": "...",
      "plants": [
        {
          "name": "...",
          "variety": "...",
          "condition": "...",
          "photo_index": 0,
          "box_2d": [ymin, xmin, ymax, xmax],
          "confidence": 0.95
        }
      ]
    }
    """
    
    result = _call_gemini([prompt] + valid_images)
    all_plants = result.get("plants", [])
    garden_name = result.get("suggested_garden_name", "")
    
    # Filter plants based on 60% confidence threshold
    filtered_plants = [p for p in all_plants if p.get("confidence", 0) >= 0.6]
    
    return filtered_plants, garden_name

def analyze_garden_overview(image_list: List[bytes], last_update_recommendation: Optional[str] = None) -> dict:
    """
    Provides a high-level overview of the garden.
    """
    valid_images = []
    for img_bytes in image_list:
        try:
            valid_images.append(Image.open(io.BytesIO(img_bytes)))
        except:
            continue
            
    if not valid_images:
        return {}

    prompt = f"""
    Analyze these garden photos and provide a high-level overview.
    Previous Recommendation: {last_update_recommendation or 'None'}

    Provide:
    1. hydration (Low/Medium/High)
    2. exposure (Low/Medium/High)
    3. vibrancy (Low/Medium/High)
    4. immediate_changes
    5. growth_trend
    6. disease_overview
    7. general_suggestions

    Return ONLY JSON:
    {{
      "summary": "comma separated summary (e.g. vibrant, healthy, full of colors)",
      "hydration": "Low/Medium/High",
      "exposure": "Low/Medium/High",
      "vibrancy": "Low/Medium/High",
      "temperature": "e.g. 24°C",
      "humidity": "e.g. 60%",
      "immediate_changes": "...",
      "growth_trend": "...",
      "disease_overview": "...",
      "general_suggestions": "..."
    }}
    """
    return _call_gemini([prompt] + valid_images)

def analyze_plant_detail(plant_image_bytes: bytes, plant_name: str, last_plant_recommendation: Optional[str] = None) -> dict:
    """
    Detailed diagnosis for a specific plant.
    """
    try:
        img = Image.open(io.BytesIO(plant_image_bytes))
    except:
        return {}

    prompt = f"""
    Detailed analysis for {plant_name}.
    Previous Recommendation: {last_plant_recommendation or 'None'}

    Provide:
    1. is_valid_plant (boolean)
    2. soil_quality
    3. disease
    4. pot_assessment
    5. pruning_needed
    6. growth_comparison
    7. recommendation

    Return ONLY JSON:
    {{
      "is_valid_plant": true,
      "soil_quality": "...",
      "disease": "...",
      "pot_assessment": "...",
      "pruning_needed": "...",
      "growth_comparison": "...",
      "recommendation": "..."
    }}
    """
    return _call_gemini([prompt, img])
