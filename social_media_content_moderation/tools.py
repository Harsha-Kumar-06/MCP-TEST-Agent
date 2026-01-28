import os
import requests
from bs4 import BeautifulSoup
from google.genai import Client, types
from dotenv import load_dotenv

# Load env to get API Key for the image analysis tool
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def fetch_web_page_content(url: str) -> str:
    """Visits a URL and returns the text content of the page.

    Useful for checking if a website contains scams, phishing, or bad content.

    Args:
        url (str): The URL of the webpage to fetch content from.

    Returns:
        str: The extracted text content from the webpage, limited to 5000 characters.
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Kill all script and style elements
        for script in soup(["script", "style"]):
            script.decompose()    

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit length to avoid context window overflow (e.g., first 5000 chars)
        print(f"Fetched content length from {url}: {len(text)} characters")
        print(text[:500])  # Print first 500 chars for debugging
        return text[:5000]
    
    except Exception as e:
        return f"Error fetching URL {url}: {str(e)}"

def analyze_image_from_url(image_url: str) -> str:
    """
    Downloads an image from a URL and analyzes it for safety, objects, and text (OCR).
    Returns a text description of what is in the image.
    """
    try:
        # 1. Download the image
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        image_bytes = response.content

        # 2. Use Gemini Client directly to analyze the image bytes
        # We use a separate client instance here to act as the "eye" of the tool.
        client = Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        
        prompt = """
        Analyze this image for content moderation.
        1. List any text visible (OCR).
        2. Describe the visual content.
        3. Check for specific safety issues: Nudity, Violence, Hate Symbols, Drugs.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    parts=[
                        types.Part(text=prompt),
                        types.Part(inline_data=types.Blob(
                            mime_type=response.headers.get('Content-Type', 'image/jpeg'),
                            data=image_bytes
                        ))
                    ]
                )
            ]
        )
        
        return response.text
        
    except Exception as e:
        return f"Error analyzing image {image_url}: {str(e)}"
