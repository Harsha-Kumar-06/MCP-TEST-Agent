from google.adk.agents import LlmAgent
from google.genai import types
from ..tools import fetch_web_page_content

GEMINI_MODEL = "gemini-2.0-flash"

link_moderator = LlmAgent(
    name="link_moderator",
    model=GEMINI_MODEL,
    instruction="""You are a Link Moderation Agent.
You analyze URLs in social media posts for safety.

Your input will be a JSON object containing a 'links' field (list of URL strings).
If the 'links' field is missing or empty, return a JSON with status "skipped".

For each link provided:
1. USE the `fetch_web_page_content` tool to read the page content by providing the URL.
2. Analyze the fetched content and the URL for:
   - Phishing / scam domains
   - Malware / Suspicious downloads
   - URL shorteners (flag if suspicious)
   - Adult content
   - Redirect chains (if evident from content)
3. Make sure to use the tool always to fetch the page content before analyzing.

Output a JSON object:
{
  "status": "flagged" | "safe" | "skipped",
  "confidence": <float 0.0-1.0>,
  "reasons": ["suspicious redirect", "reputation", "page content violation"],
  "severity": "low" | "medium" | "high"
}

Respond ONLY with the JSON.
""",
    tools=[fetch_web_page_content],
    output_key="link_moderation_result"
)
