import uvicorn
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.sessions import InMemorySessionService
from google.adk import Runner
from google.genai import types
from pydantic import BaseModel
import uuid
from social_media_marketing import root_agent

load_dotenv()

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

session_uri = os.getenv("SESSION_SERVICE_URI", None)
session_service = InMemorySessionService()

web_interface_enabled = os.getenv("SERVE_WEB_INTERFACE", "False").lower() in (
    "true",
    "1",
)

app_args = {"agents_dir": AGENT_DIR, "web": web_interface_enabled}

if session_uri:
    app_args["session_service_uri"] = session_uri

app: FastAPI = get_fast_api_app(**app_args)

# Mount static files for custom UI
static_dir = os.path.join(AGENT_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve custom HTML UI
@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

app.title = "Social Media Marketing Agent"
app.description = "Analyze social media trends across Instagram, TikTok, and YouTube and formulate marketing strategies"
app.version = "1.0.0"

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    api_key = os.getenv("GOOGLE_API_KEY")
    return {
        "status": "healthy",
        "service": "Social Media Marketing Agent",
        "framework": "Google ADK",
        "api_key_configured": bool(api_key and api_key != "API_KEY"),
    }


# Request models
class QueryRequest(BaseModel):
    question: str
    sessionId: str
    userId: str


class HistoryRequest(BaseModel):
    sessionId: str
    userId: str


@app.post("/api/session")
async def register_session(user_id: str, session_id: str):
    """Register a new session for a user."""
    app_name = "social_media_marketing"
    try:
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        return {"success": True, "session_id": session_id, "user_id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/query")
async def query_agent(request: QueryRequest):
    """Run a query through the root_agent using provided sessionId and userId.

    Uses the provided sessionId and userId from request.
    Collects textual parts from streamed events and returns them.
    """
    question = (request.question or "").strip()
    session_id = (request.sessionId or "").strip()
    user_id = (request.userId or "").strip()

    if not question:
        return {"success": False, "error": "question is required"}
    if not session_id:
        return {"success": False, "error": "sessionId is required"}
    if not user_id:
        return {"success": False, "error": "userId is required"}

    app_name = "social_media_marketing"
    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)

    new_message = types.Content(role="user", parts=[types.Part(text=question)])

    # Collect text from events
    collected = []
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=new_message):
            # robust extraction of text from event
            try:
                content = getattr(event, 'content', None)
                if content:
                    parts = getattr(content, 'parts', None) or getattr(content, 'parts_', None)
                    if parts:
                        for p in parts:
                            text = getattr(p, 'text', None) or getattr(p, 'value', None)
                            if text:
                                collected.append(str(text))
                        continue

                # fallback to any available string fields
                if hasattr(event, 'message'):
                    collected.append(str(getattr(event, 'message')))
                else:
                    collected.append(str(event))
            except Exception:
                # ignore per-event parse errors
                continue
    except Exception as e:
        return {"success": False, "error": f"agent run failed: {e}"}

    final_text = "\n\n".join(collected).strip()

    return {"success": True, "session_id": session_id, "response": final_text}


@app.get("/api/history")
async def get_history(session_id: str, user_id: str):
    try:
        session = await session_service.get_session(
            app_name="social_media_marketing",
            session_id=session_id,
            user_id=user_id
        )
        if session:
            conversation_history = session.events

            return {"success": True, "session_id": session_id, "user_id": user_id, "messages": conversation_history}
        else:
            return {"success": True, "session_id": session_id, "user_id": user_id, "messages": []}
    except Exception as e:
        return {"success": False, "error": str(e), "messages": []}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))