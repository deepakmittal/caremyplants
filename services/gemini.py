import os
import json
from google import genai
from google.genai import types
from PIL import Image
import io
from typing import List, Optional
from dotenv import load_dotenv

# Determine environment
IS_CLOUD_RUN = os.getenv('K_SERVICE') is not None

# Try loading from various possible locations for the .env file
dotenv_locations = []
if IS_CLOUD_RUN:
    dotenv_locations.append(os.path.join('/keys', '.env'))

dotenv_locations.extend([
    os.path.join(os.path.dirname(__file__), '..', 'keys', '.env'), # Local dev (one level up)
    os.path.join(os.getcwd(), 'keys', '.env'),                   # Docker /app/keys/
])

for loc in dotenv_locations:
    if os.path.exists(loc):
        load_dotenv(loc)
        break
else:
    load_dotenv() # Fallback to default behavior

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

def _get_client():
    """Return a configured Gemini client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set!")
        return None
    return genai.Client(api_key=api_key)

def _call_gemini(contents: list) -> dict:
    """Helper to call Gemini and parse JSON response."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    client = _get_client()
    if not client:
        return {}

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
        )

        if not response or not response.text:
            print(f"Error: Gemini returned an empty response.")
            return {}

        text = response.text.strip()

        # Clean up Markdown JSON blocks
        if text.startswith("```json"):
            text = text[7:].split("```")[0].strip()
        elif text.startswith("```"):
            text = text[3:].split("```")[0].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print(f"Error: Failed to parse Gemini response as JSON. Raw text: {text[:500]}...")
            return {}
    except Exception as e:
        print(f"Exception during Gemini call: {str(e)}")
        return {}

def _pil_to_part(img: Image.Image) -> types.Part:
    """Convert a PIL image to a Gemini Part."""
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

def identify_plants_with_gemini(image_list: List[bytes]):
    """
    Identifies plants and suggests a garden name.
    """
    parts = []
    for img_bytes in image_list:
        try:
            img = Image.open(io.BytesIO(img_bytes))
            parts.append(_pil_to_part(img))
        except:
            continue

    if not parts:
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

    result = _call_gemini([prompt] + parts)
    all_plants = result.get("plants", [])
    garden_name = result.get("suggested_garden_name", "")

    # Filter plants based on 60% confidence threshold
    filtered_plants = [p for p in all_plants if p.get("confidence", 0) >= 0.6]

    return filtered_plants, garden_name

def analyze_garden_overview(image_list: List[bytes], last_update_recommendation: Optional[str] = None) -> dict:
    """
    Provides a high-level overview of the garden.
    """
    parts = []
    for img_bytes in image_list:
        try:
            img = Image.open(io.BytesIO(img_bytes))
            parts.append(_pil_to_part(img))
        except:
            continue

    if not parts:
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
    8. pest_presence (boolean)
    9. weed_presence (boolean)
    10. flowering_status (boolean)

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
      "general_suggestions": "...",
      "pest_presence": true,
      "weed_presence": false,
      "flowering_status": true
    }}
    """
    return _call_gemini([prompt] + parts)

def analyze_plant_detail(plant_image_bytes: bytes, plant_name: str, last_plant_recommendation: Optional[str] = None) -> dict:
    """
    Detailed diagnosis for a specific plant.
    """
    try:
        img = Image.open(io.BytesIO(plant_image_bytes))
        part = _pil_to_part(img)
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
    return _call_gemini([prompt, part])
