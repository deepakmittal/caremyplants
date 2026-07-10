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
        response = client.generate_content(
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

def assess_garden_health_with_ai(image_list: List[bytes]) -> dict:
    """
    Provides a detailed garden health assessment using a star rating and categorical statuses.
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
    Analyze the provided garden photos and generate a detailed health assessment.

    1.  **Overall Score:** Provide a single integer score from 1 to 5 for the entire garden, where 5 is a perfect, flourishing garden and 1 is a garden in critical need of attention.

    2.  **Metric Statuses:** For each category below, provide a concise status from the given options.

        -   **WATERING:** Choose one: `Overwatered`, `Properly Watered`, `Underwatered`
        -   **SUN_EXPOSURE:** Choose one: `Too Sunny`, `Sunny`, `Dark`
        -   **SOIL_QUALITY:** Choose one: `Rich`, `Balanced`, `Poor`
        -   **VITALITY:** Choose one: `Thriving`, `Stable`, `Struggling`
        -   **LEAF_CARE:** Choose one: `Pristine`, `Dusty`, `Diseased`
        -   **POT_STATUS:** Choose one: `Spacious`, `Adequate`, `Cramped`
        -   **PRUNING:** Choose one: `Well-Maintained`, `Needs Light Pruning`, `Overgrown`

    Return ONLY a JSON object in the following format:
    {{
      "score": <integer from 1 to 5>,
      "metrics": {{
        "WATERING": "...",
        "SUN_EXPOSURE": "...",
        "SOIL_QUALITY": "...",
        "VITALITY": "...",
        "LEAF_CARE": "...",
        "POT_STATUS": "...",
        "PRUNING": "..."
      }}
    }}
    """
    return _call_gemini([prompt] + parts)


def identify_plants_with_gemini(image_list: List[bytes], existing_plants: Optional[List[str]] = None):
    """
    Identifies plants and suggests a garden name.
    If existing_plants is provided, it tries to match identified plants to existing names.
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
        
    existing_plants_text = ""
    if existing_plants:
        existing_plants_text = f"\nHere is a list of existing plants in this garden: {', '.join(existing_plants)}.\nIf you identify a plant that matches one of these existing plants, you MUST use the exact existing name. If it is a new plant, give it a new name."

    prompt = f"""
    Exhaustively identify EVERY individual plant visible in these garden photos. 
    Include plants in the foreground, background, and those partially obscured. 
    {existing_plants_text}

    For each plant provide:
    1. Common Name and Variety.
    2. Condition: Small comma separated list (e.g., "vibrant, healthy").
    3. photo_index: 0-based index of the photo.
    4. box_2d: bounding box [ymin, xmin, ymax, xmax] (0-1000).
    5. confidence: a float between 0 and 1 representing your confidence in this identification.

    Return ONLY a JSON object:
    {{
      "suggested_garden_name": "...",
      "plants": [
        {{
          "name": "...",
          "variety": "...",
          "condition": "...",
          "photo_index": 0,
          "box_2d": [ymin, xmin, ymax, xmax],
          "confidence": 0.95
        }}
      ]
    }}
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
    8. needs_watering (boolean)
    9. needs_fertilizer (boolean)
    10. has_pests (boolean)
    11. has_weeds (boolean)
    12. has_disease (boolean)
    13. needs_sunlight (boolean)

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
      "needs_watering": true,
      "needs_fertilizer": false,
      "has_pests": false,
      "has_weeds": true,
      "has_disease": false,
      "needs_sunlight": true
    }}
    """
    return _call_gemini([prompt] + parts)

def analyze_plant_detail(plant_image_bytes: bytes, plant_name: str, last_plant_recommendation: Optional[str] = None, last_plant_condition: Optional[str] = None) -> dict:
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
    Previous Condition: {last_plant_condition or 'None'}
    Previous Recommendation: {last_plant_recommendation or 'None'}

    Compare the plant's current state with the 'Previous Condition'. Specifically identify any improvements or degradations.

    Provide:
    1. is_valid_plant (boolean)
    2. soil_quality
    3. disease
    4. pot_assessment
    5. pruning_needed
    6. growth_comparison
    7. changes_from_previous (Document explicitly what improvements or regressions happened since the previous update based on the image and previous condition)
    8. recommendation

    Return ONLY JSON:
    {{
      "is_valid_plant": true,
      "soil_quality": "...",
      "disease": "...",
      "pot_assessment": "...",
      "pruning_needed": "...",
      "growth_comparison": "...",
      "changes_from_previous": "...",
      "recommendation": "..."
    }}
    """
    return _call_gemini([prompt, part])

def generate_garden_visualization_with_gemini(
    image_bytes: bytes,
    plants: List[dict],
    recommendations: List[str]
) -> Optional[bytes]:
    """
    Generates a garden visualization with product recommendations.

    Args:
        image_bytes: The original garden photo.
        plants: A list of dictionaries, where each dictionary represents a plant
                and contains a 'box_2d' key with the bounding box coordinates.
        recommendations: A list of recommendations to display on the image.

    Returns:
        The generated image as bytes, or None if an error occurred.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        part = _pil_to_part(img)
    except:
        return None

    # Construct the prompt with plant locations and recommendations
    plant_locations = []
    for i, plant in enumerate(plants):
        if "box_2d" in plant:
            plant_locations.append(f"  - Plant {i+1}: at bounding box {plant['box_2d']}")

    recommendations_text = "\n".join(f"- {rec}" for rec in recommendations)

    prompt = f"""
    Analyze the provided garden photo and the following information to generate a new image with helpful visualizations and recommendations.

    **Objective:** Create an enhanced version of the original image that visually highlights areas for improvement and displays actionable recommendations. The new image should be a photorealistic rendering of the garden with the suggested changes applied.

    **Information:**

    *   **Plant Locations:**
        {chr(10).join(plant_locations)}

    *   **Recommendations:**
        {recommendations_text}

    **Instructions for Image Generation:**

    1.  **Photorealistic Rendering:** The output must be a high-quality, photorealistic image, not a cartoon or drawing. It should look like a real photograph of the improved garden.
    2.  **Apply Recommendations:** Modify the original image to reflect the recommendations. For example:
        *   If a plant needs watering, show the soil as moist.
        *   If a plant needs pruning, show it as neatly trimmed.
        *   If a new tool or product is recommended, visually integrate it into the scene in a natural way (e.g., a watering can next to a thirsty plant, a bag of fertilizer nearby).
    3.  **Visual Indicators:** Use subtle visual cues to draw attention to the improved areas. You can use arrows, circles, or highlighted regions, but they must be tastefully integrated into the image.
    4.  **Text Overlay:** Overlay the recommendations as text directly onto the image. The text should be legible, well-placed, and not obscure important parts of the garden.

    **Output:**

    *   Return only the generated image. Do not return any text, JSON, or other data.
    """

    model_name = "gemini-1.5-flash"  # Or another suitable model
    client = _get_client()
    if not client:
        return None

    try:
        response = client.generate_content(
            model=model_name,
            contents=[prompt, part],
        )

        if not response or not response.parts:
            print("Error: Gemini returned an empty response for visualization.")
            return None

        # Assuming the first part is the image
        image_part = response.parts[0]
        if image_part.mime_type.startswith("image/"):
            return image_part.data
        else:
            print(f"Error: Gemini did not return an image. Mime type: {image_part.mime_type}")
            return None

    except Exception as e:
        print(f"Exception during Gemini visualization call: {str(e)}")
        return None
