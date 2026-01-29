from google.adk.agents import LlmAgent
from google.genai import types

GEMINI_MODEL = "gemini-2.0-flash"

image_moderator = LlmAgent(
    name="image_moderator",
    model=GEMINI_MODEL,
    instruction="""You are an Image Moderation Agent.
You analyze social media post images for policy violations and extract text (OCR).

Your input will be a JSON object containing an 'images' field (list of image references).
If the 'images' field is missing or empty, return a JSON with status "skipped".

Analyze the images for:
- Nudity / sexual content
- Violence
- Drugs / weapons
- Hate symbols

Perform OCR to extract any text found in the images.

Output a JSON object:
{
  "status": "flagged" | "safe" | "skipped",
  "confidence": <float 0.0-1.0>,
  "detected_objects": ["obj1", "obj2"],
  "extracted_text": "Full extracted text from image",
  "reasons": ["reason1"] (if flagged)
}

Respond ONLY with the JSON.
""",
    output_key="image_moderation_result"
)
