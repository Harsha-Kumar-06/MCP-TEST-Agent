import json
import uuid
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import your agent
# Note: When running this, ensure your python path is set correctly or run as a module
from .agent import root_agent

app = FastAPI(title="Social Media Content Moderation Agent")

# --- ADK Setup ---
session_service = InMemorySessionService()
# We create a runner instance for our root agent
runner = Runner(
    agent=root_agent,
    app_name="social_media_moderator",
    session_service=session_service
)

# --- Data Models ---
class ModerationRequest(BaseModel):
    text: Optional[str] = None
    images: Optional[List[str]] = []
    links: Optional[List[str]] = []

class ModerationResponse(BaseModel):
    final_decision: str
    severity: str
    violations: List[str]
    action: str
    explanation: str

# --- Endpoints ---

@app.post("/moderate", response_model=ModerationResponse)
async def moderate_content(request: ModerationRequest):
    """
    Moderates social media content (text, images, links).
    """
    
    # 1. Prepare Session
    # We generate a unique session ID for every request to keep states (text_result, image_result) isolated.
    session_id = str(uuid.uuid4())
    user_id = "api_user"
    
    session = await session_service.create_session(
        app_name="social_media_moderator",
        user_id=user_id,
        session_id=session_id
    )

    # 2. Format Input for the Agent
    # The Parallel agents all expect a JSON structure. 
    # We pass the incoming request model directly as a JSON string.
    user_input_json = request.model_dump_json()
    
    agent_message = types.Content(
        role="user",
        parts=[types.Part(text=user_input_json)]
    )

    # 3. Run the Agent
    try:
        # Collect the response. The agent returns a list of events.
        # We process them async to find the final answer.
        final_text = ""
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=agent_message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text
        
        if not final_text:
            raise HTTPException(status_code=500, detail="Agent returned no response.")

        # 4. Parse Response
        # The Synthesis Agent returns a JSON string. We parse it back to a dictionary.
        # Clean up any potential markdown formatting (```json ... ```)
        cleaned_text = final_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        result_data = json.loads(cleaned_text.strip())
        
        return result_data

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to parse agent response: {final_text}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}