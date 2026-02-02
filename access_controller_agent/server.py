"""
FastAPI server for the Access Controller agent. Exposes /request (or /access) and /health.
"""
import os
import uuid
import logging
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AccessController")

app = FastAPI(title="Access Controller Agent")

session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="access_controller",
    session_service=session_service,
)


class AccessRequest(BaseModel):
    """Incoming message (e.g. email body or direct request)."""
    message: str


class AccessResponse(BaseModel):
    """Agent response text."""
    response: str


@app.post("/request", response_model=AccessResponse)
async def handle_request(req: AccessRequest):
    """
    Handle an access request (e.g. "Grant john@company.com access to project PROJ on Jira").
    Use a new session per request for isolation.
    """
    session_id = str(uuid.uuid4())
    user_id = "api_user"

    await session_service.create_session(
        app_name="access_controller",
        user_id=user_id,
        session_id=session_id,
    )

    agent_message = types.Content(
        role="user",
        parts=[types.Part(text=req.message)],
    )

    try:
        final_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=agent_message,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text or ""

        if not final_text:
            final_text = "No response generated."

        return AccessResponse(response=final_text.strip())
    except Exception as e:
        logger.exception("Agent run failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/access", response_model=AccessResponse)
async def handle_access(req: AccessRequest):
    """Alias for /request for semantic clarity."""
    return await handle_request(req)


@app.get("/health")
def health():
    return {"status": "ok"}
