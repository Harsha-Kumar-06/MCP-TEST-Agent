"""
CorpAssist - Custom FastAPI Web Application

A professional chat interface for the CorpAssist router agent.
Includes authentication, audit logging, specialist chat, and enterprise features.
"""

import asyncio
import os
import uuid
import secrets
import json
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Dict, Optional, List, Set

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request, Header, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from helpdesk_bot import root_agent
from helpdesk_bot.tools.escalation_tools import close_servicenow_incident
from auth import auth_manager, audit_logger, User, AuthToken

# Load environment variables
load_dotenv()

# Configuration
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8080")

# Store active sessions
sessions: Dict[str, dict] = {}
session_service = InMemorySessionService()
runner = None

# =============================================================================
# Agent Conversation Memory
# =============================================================================
# Store conversation history per agent per session
# Format: {session_id: {agent_name: [{"role": "user/assistant", "content": "...", "timestamp": "..."}]}}
agent_conversations: Dict[str, Dict[str, List[dict]]] = {}

# Track current active agent per session
active_agent_per_session: Dict[str, str] = {}

# =============================================================================
# Escalation & Specialist Session Management
# =============================================================================

# Store escalation sessions: escalation_id -> session data
escalation_sessions: Dict[str, dict] = {}

# Reverse lookup: ServiceNow incident number -> escalation_id
incident_to_escalation: Dict[str, str] = {}

# Store active WebSocket connections for real-time chat
# escalation_id -> {"user": WebSocket, "specialist": WebSocket}
active_connections: Dict[str, dict] = {}

# Chat history for escalation sessions
chat_histories: Dict[str, List[dict]] = {}

# Security
security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    global runner
    runner = Runner(
        agent=root_agent,
        app_name="helpdesk_bot",
        session_service=session_service,
    )
    print("CorpAssist initialized successfully!")
    yield
    print("Shutting down...")


app = FastAPI(
    title="CorpAssist",
    description="Workplace Support Router Agent",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatMessage(BaseModel):
    message: str
    session_id: str = None
    user_timezone: str = None
    user_local_time: str = None
    user_local_date: str = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    routed_to: Optional[str] = None
    user: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: dict
    expires_at: str


# =============================================================================
# Authentication Helpers
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[User]:
    """Extract and validate user from token."""
    if not REQUIRE_AUTH:
        # Return anonymous user when auth is disabled
        return User(
            employee_id="ANON",
            email="anonymous@company.com",
            full_name="Anonymous User",
            department="Unknown",
            role="employee",
        )
    
    if not credentials:
        return None
        
    user = auth_manager.validate_token(credentials.credentials)
    return user


async def require_auth(
    user: Optional[User] = Depends(get_current_user),
) -> User:
    """Require authenticated user."""
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please login.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# =============================================================================
# Authentication Endpoints
# =============================================================================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return token.
    
    Demo credentials:
    - john.doe@company.com / demo123
    - jane.smith@company.com / demo123
    - admin@company.com / admin123
    """
    auth_token = auth_manager.authenticate({
        "email": request.email,
        "password": request.password,
    })
    
    if not auth_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    
    return LoginResponse(
        token=auth_token.token,
        user={
            "employee_id": auth_token.user.employee_id,
            "email": auth_token.user.email,
            "full_name": auth_token.user.full_name,
            "department": auth_token.user.department,
            "role": auth_token.user.role,
        },
        expires_at=auth_token.expires_at.isoformat(),
    )


@app.post("/api/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout and revoke token."""
    if credentials:
        auth_manager.logout(credentials.credentials)
    return {"status": "logged_out"}


@app.get("/api/auth/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current authenticated user."""
    return {
        "employee_id": user.employee_id,
        "email": user.email,
        "full_name": user.full_name,
        "department": user.department,
        "role": user.role,
        "manager_email": user.manager_email,
        "location": user.location,
    }


@app.get("/api/auth/config")
async def get_auth_config():
    """Get authentication configuration for frontend."""
    return {
        "auth_required": REQUIRE_AUTH,
        "auth_method": os.getenv("AUTH_METHOD", "basic"),
        "sso_enabled": os.getenv("SSO_ENABLED", "false").lower() == "true",
    }


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat interface."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Process a chat message and return response."""
    global runner
    
    # Check auth if required
    if REQUIRE_AUTH and not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Create or get session
        session_id = message.session_id
        if not session_id or session_id not in sessions:
            session_id = str(uuid.uuid4())
            session = await session_service.create_session(
                app_name="helpdesk_bot",
                user_id=session_id,
            )
            sessions[session_id] = {
                "adk_session": session,
                "user": user,
            }
        
        session = sessions[session_id]["adk_session"]
        
        # Add user context to message for personalized responses
        user_context = ""
        if user and user.employee_id != "ANON":
            user_context = f"\n[User Context: {user.full_name}, {user.department}, {user.role}]\n"
        
        # Add timezone context if provided
        if message.user_timezone:
            user_context += f"[User Timezone: {message.user_timezone}]"
            if message.user_local_time:
                user_context += f" [User's Local Time: {message.user_local_time}]"
            if message.user_local_date:
                user_context += f" [User's Local Date: {message.user_local_date}]"
            user_context += "\n"
        
        # Create user message
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_context + message.message)]
        )
        
        # Get response from agent
        response_text = ""
        routed_to = None
        
        async for event in runner.run_async(
            session_id=session.id,
            user_id=session_id,
            new_message=content,
        ):
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
            
            # Try to detect which agent handled the request
            if hasattr(event, "author"):
                if event.author and event.author != "helpdesk_router":
                    routed_to = event.author
        
        if not response_text:
            response_text = "I received your message but couldn't generate a response. Please try again."
        
        # Log escalation detection
        import re
        esc_match = re.search(r'ESC-\d{14}', response_text)
        if esc_match:
            print(f"[ESCALATION DETECTED] Response contains: {esc_match.group()}")
            print(f"[ESCALATION] Full response snippet: {response_text[:500]}")
        
        # Store conversation in agent-specific memory
        if session_id not in agent_conversations:
            agent_conversations[session_id] = {}
        
        agent_key = routed_to or "helpdesk_router"
        if agent_key not in agent_conversations[session_id]:
            agent_conversations[session_id][agent_key] = []
        
        # Add user message to agent history
        agent_conversations[session_id][agent_key].append({
            "role": "user",
            "content": message.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add assistant response to agent history
        agent_conversations[session_id][agent_key].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update active agent for this session
        active_agent_per_session[session_id] = agent_key
        
        # Audit log the interaction
        if user:
            client_ip = request.client.host if request.client else None
            audit_logger.log_chat(user, message.message, response_text, client_ip)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            routed_to=routed_to,
            user=user.full_name if user else None,
        )
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            response=f"Sorry, an error occurred: {str(e)}. Please make sure GOOGLE_API_KEY is set in your .env file.",
            session_id=message.session_id or str(uuid.uuid4()),
            routed_to=None
        )


@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    global runner
    
    await websocket.accept()
    
    # Create session if needed
    if session_id not in sessions:
        session = await session_service.create_session(
            app_name="helpdesk_bot",
            user_id=session_id,
        )
        sessions[session_id] = {"adk_session": session}
    
    session = sessions[session_id]["adk_session"]
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            
            # Create user message
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=data)]
            )
            
            # Stream response
            async for event in runner.run_async(
                session_id=session.id,
                user_id=session_id,
                new_message=content,
            ):
                if hasattr(event, "content") and event.content:
                    if hasattr(event.content, "parts"):
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                await websocket.send_json({
                                    "type": "chunk",
                                    "content": part.text
                                })
            
            # Signal end of response
            await websocket.send_json({"type": "done"})
            
    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "corpassist"}


@app.get("/api/time")
async def get_current_time(timezone: str = None):
    """
    Get current server time, optionally in a specific timezone.
    
    Args:
        timezone: Optional timezone name (e.g., "America/New_York", "Europe/London")
    
    Returns:
        dict: Current time information
    """
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo
    
    # Get server time
    server_time = datetime.now()
    
    result = {
        "server_time": server_time.isoformat(),
        "server_time_formatted": server_time.strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week": server_time.strftime("%A"),
        "date": server_time.strftime("%B %d, %Y"),
    }
    
    # If timezone provided, also return time in that timezone
    if timezone:
        try:
            user_tz = ZoneInfo(timezone)
            user_time = datetime.now(user_tz)
            result["user_timezone"] = timezone
            result["user_time"] = user_time.isoformat()
            result["user_time_formatted"] = user_time.strftime("%Y-%m-%d %H:%M:%S")
            result["user_day_of_week"] = user_time.strftime("%A")
            result["user_date"] = user_time.strftime("%B %d, %Y")
        except Exception as e:
            result["timezone_error"] = f"Invalid timezone: {timezone}"
    
    return result


@app.post("/api/session/new")
async def new_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    session = await session_service.create_session(
        app_name="helpdesk_bot",
        user_id=session_id,
    )
    sessions[session_id] = {"adk_session": session}
    # Initialize agent conversation storage for this session
    agent_conversations[session_id] = {}
    return {"session_id": session_id}


# =============================================================================
# Agent Conversation Memory API
# =============================================================================

@app.get("/api/session/{session_id}/agents")
async def get_agent_conversations(session_id: str):
    """
    Get all agents that have conversations in this session.
    Returns list of agents with message counts and last activity.
    """
    if session_id not in agent_conversations:
        return {"agents": [], "active_agent": None}
    
    agent_list = []
    for agent_name, messages in agent_conversations[session_id].items():
        if messages:
            last_message = messages[-1]
            agent_list.append({
                "agent": agent_name,
                "message_count": len(messages),
                "last_activity": last_message.get("timestamp"),
                "preview": last_message.get("content", "")[:100] + "..." if len(last_message.get("content", "")) > 100 else last_message.get("content", "")
            })
    
    # Sort by last activity
    agent_list.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
    
    return {
        "agents": agent_list,
        "active_agent": active_agent_per_session.get(session_id)
    }


@app.get("/api/session/{session_id}/agent/{agent_name}/history")
async def get_agent_history(session_id: str, agent_name: str):
    """
    Get the conversation history for a specific agent in this session.
    Used when switching back to a previous agent conversation.
    """
    if session_id not in agent_conversations:
        return {"messages": [], "agent": agent_name}
    
    messages = agent_conversations[session_id].get(agent_name, [])
    
    return {
        "messages": messages,
        "agent": agent_name,
        "message_count": len(messages)
    }


@app.post("/api/session/{session_id}/agent/{agent_name}/switch")
async def switch_to_agent(session_id: str, agent_name: str):
    """
    Switch the active agent for a session.
    Returns the conversation history for that agent.
    """
    if session_id not in agent_conversations:
        return {"success": False, "error": "Session not found"}
    
    if agent_name not in agent_conversations[session_id]:
        return {"success": False, "error": "No conversation with this agent"}
    
    # Update active agent
    active_agent_per_session[session_id] = agent_name
    
    messages = agent_conversations[session_id].get(agent_name, [])
    
    return {
        "success": True,
        "agent": agent_name,
        "messages": messages,
        "message_count": len(messages)
    }


# =============================================================================
# Escalation Session Management
# =============================================================================

def create_escalation_session(
    escalation_id: str,
    department: str,
    urgency: str,
    issue_summary: str,
    employee_id: str,
    user_session_id: str = None,
    user_info: dict = None,
    servicenow_incident: str = None,
    servicenow_only: bool = False,
) -> dict:
    """
    Create an escalation session for specialist chat.
    
    Args:
        servicenow_only: If True, this is a ServiceNow-only ticket without live chat capability
    
    Returns:
        dict: Session info including specialist_token and specialist_url
    """
    # Generate secure token for specialist access
    specialist_token = secrets.token_urlsafe(32)
    
    session_data = {
        "escalation_id": escalation_id,
        "specialist_token": specialist_token,
        "department": department,
        "urgency": urgency,
        "issue_summary": issue_summary,
        "employee_id": employee_id,
        "user_session_id": user_session_id,
        "user": user_info,
        "servicenow_incident": servicenow_incident,
        "servicenow_only": servicenow_only,  # Track if this is ServiceNow-only
        "created_at": datetime.now().isoformat(),
        "status": "waiting_for_specialist" if not servicenow_only else "servicenow_only",
        "specialist_joined": False,
        "specialist_name": None,
        "user_connected": False,
        "user_disconnected": False,
        "specialist_disconnected": False,
    }
    
    # Store session
    escalation_sessions[escalation_id] = session_data
    
    # Create reverse lookup for ServiceNow incident
    if servicenow_incident:
        incident_to_escalation[servicenow_incident] = escalation_id
    
    # Initialize chat history
    chat_histories[escalation_id] = []
    
    # Add initial system message about waiting state
    if not servicenow_only:
        chat_histories[escalation_id].append({
            "role": "system",
            "content": "Session created. Waiting for specialist to connect...",
            "timestamp": datetime.now().isoformat(),
        })
    else:
        chat_histories[escalation_id].append({
            "role": "system",
            "content": "ServiceNow ticket created. A specialist will respond via ServiceNow.",
            "timestamp": datetime.now().isoformat(),
        })
    
    # Generate specialist URL (only if not ServiceNow-only)
    specialist_url = f"{APP_BASE_URL}/specialist?escalation_id={escalation_id}&token={specialist_token}" if not servicenow_only else None
    
    return {
        "escalation_id": escalation_id,
        "specialist_token": specialist_token,
        "specialist_url": specialist_url,
        "servicenow_only": servicenow_only,
        "session_data": session_data,
    }


def get_escalation_session(escalation_id: str) -> Optional[dict]:
    """Get escalation session by ID."""
    return escalation_sessions.get(escalation_id)


def validate_specialist_token(escalation_id: str, token: str) -> bool:
    """Validate specialist access token."""
    session = escalation_sessions.get(escalation_id)
    if not session:
        return False
    return session.get("specialist_token") == token


# =============================================================================
# Specialist API Endpoints
# =============================================================================

class SpecialistValidation(BaseModel):
    escalation_id: str
    token: str


@app.get("/specialist", response_class=HTMLResponse)
async def specialist_page():
    """Serve the specialist chat interface."""
    with open("static/specialist.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/specialist/validate")
async def validate_specialist_session(data: SpecialistValidation):
    """
    Validate specialist session and return escalation details.
    Called when specialist opens the chat link.
    """
    if not validate_specialist_token(data.escalation_id, data.token):
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    session = escalation_sessions[data.escalation_id]
    
    # Check if session is already closed or resolved
    session_status = session.get("status", "")
    if session_status in ("closed", "resolved"):
        raise HTTPException(
            status_code=410,  # 410 Gone - resource no longer available
            detail=f"This escalation session has already ended (status: {session_status}). Please wait for a new escalation request."
        )
    
    # Mark specialist as joined
    session["specialist_joined"] = True
    
    return {
        "valid": True,
        "session_id": session.get("user_session_id"),
        "escalation_id": data.escalation_id,
        "department": session.get("department"),
        "urgency": session.get("urgency"),
        "issue_summary": session.get("issue_summary"),
        "created_at": session.get("created_at"),
        "servicenow_incident": session.get("servicenow_incident"),
        "servicenow_url": f"https://company.service-now.com/incident.do?sys_id={session.get('servicenow_incident')}" if session.get("servicenow_incident") else None,
        "user": session.get("user"),
    }


# =============================================================================
# User Escalation API (for page refresh recovery)
# =============================================================================

@app.get("/api/escalation/{escalation_id}/status")
async def get_escalation_status(escalation_id: str):
    """
    Get the status of an escalation session.
    Used by the frontend to check if an escalation is still active after page refresh.
    """
    session = escalation_sessions.get(escalation_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    return {
        "escalation_id": escalation_id,
        "status": session.get("status", "unknown"),
        "department": session.get("department"),
        "specialist_joined": session.get("specialist_joined", False),
        "servicenow_incident": session.get("servicenow_incident"),
        "servicenow_only": session.get("servicenow_only", False),
        "created_at": session.get("created_at"),
    }


@app.get("/api/escalation/{escalation_id}/history")
async def get_user_escalation_history(escalation_id: str):
    """
    Get chat history for a user's escalation session.
    Does not require specialist token - used for reconnecting after page refresh.
    """
    session = escalation_sessions.get(escalation_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    history = chat_histories.get(escalation_id, [])
    
    return {
        "escalation_id": escalation_id,
        "messages": history,
        "status": session.get("status"),
        "specialist_joined": session.get("specialist_joined", False),
    }


@app.get("/api/specialist/history/{escalation_id}")
async def get_specialist_chat_history(
    escalation_id: str,
    token: str = Query(...),
):
    """Get chat history for an escalation session."""
    if not validate_specialist_token(escalation_id, token):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    history = chat_histories.get(escalation_id, [])
    return {"escalation_id": escalation_id, "messages": history}


@app.post("/api/specialist/close/{escalation_id}")
async def close_specialist_session(escalation_id: str, data: dict):
    """Close an escalation session and resolve ServiceNow ticket."""
    token = data.get("token")
    if not validate_specialist_token(escalation_id, token):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    resolution_notes = data.get("resolution_notes", "Resolved via chat")
    resolution_code = data.get("resolution_code", "Solved (Permanently)")
    
    session = escalation_sessions.get(escalation_id)
    servicenow_result = None
    
    if session:
        session["status"] = "closed"
        session["closed_at"] = datetime.now().isoformat()
        session["resolution_notes"] = resolution_notes
        session["resolution_code"] = resolution_code
        
        # Close the ServiceNow ticket if one was created
        servicenow_incident = session.get("servicenow_incident")
        if servicenow_incident:
            servicenow_result = close_servicenow_incident(
                incident_number=servicenow_incident,
                resolution_notes=f"Resolved by specialist via live chat.\n\n{resolution_notes}",
                resolution_code=resolution_code
            )
            print(f"ServiceNow ticket {servicenow_incident} closure result: {servicenow_result}")
    
    # Notify connected clients
    if escalation_id in active_connections:
        for role, ws in active_connections[escalation_id].items():
            if ws:
                try:
                    await ws.send_json({"type": "session_closed"})
                except:
                    pass
    
    return {
        "status": "closed", 
        "escalation_id": escalation_id,
        "servicenow_closed": servicenow_result.get("updated", False) if servicenow_result else False
    }


# =============================================================================
# ServiceNow Webhook - Called when ticket state changes
# =============================================================================
# Configure in ServiceNow:
# 1. Go to System Policy > Events > Business Rules
# 2. Create a Business Rule on "incident" table
# 3. When: state changes to 6 (Resolved) or 7 (Closed)
# 4. Action: Send REST message to this endpoint
# =============================================================================

SERVICENOW_WEBHOOK_SECRET = os.getenv("SERVICENOW_WEBHOOK_SECRET", "")

@app.post("/api/webhook/servicenow")
async def servicenow_webhook(request: Request):
    """
    Webhook endpoint called by ServiceNow when incident state changes.
    
    Expected payload from ServiceNow:
    {
        "incident_number": "INC0012345",
        "sys_id": "abc123...",
        "state": "6",  // 6=Resolved, 7=Closed
        "close_code": "Solved (Permanently)",
        "close_notes": "Reset password and verified access",
        "resolved_by": "john.doe@company.com",
        "secret": "your_webhook_secret"  // Optional security
    }
    """
    try:
        data = await request.json()
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Validate webhook secret if configured
    if SERVICENOW_WEBHOOK_SECRET:
        provided_secret = data.get("secret") or request.headers.get("X-ServiceNow-Secret")
        if provided_secret != SERVICENOW_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    incident_number = data.get("incident_number") or data.get("number")
    state = data.get("state")
    
    if not incident_number:
        raise HTTPException(status_code=400, detail="Missing incident_number")
    
    # Find the escalation session linked to this incident
    escalation_id = incident_to_escalation.get(incident_number)
    
    if not escalation_id:
        # Try to find by iterating (fallback for incidents created before tracking)
        for esc_id, session in escalation_sessions.items():
            if session.get("servicenow_incident") == incident_number:
                escalation_id = esc_id
                incident_to_escalation[incident_number] = esc_id
                break
    
    if not escalation_id:
        return {"status": "ignored", "reason": "No matching escalation found"}
    
    session = escalation_sessions.get(escalation_id)
    if not session:
        return {"status": "ignored", "reason": "Escalation session not found"}
    
    # Check if ticket is being resolved/closed (state 6 or 7)
    if state in ["6", "7", 6, 7]:
        # Update session status
        session["status"] = "resolved"
        session["resolved_at"] = datetime.now().isoformat()
        session["resolution_notes"] = data.get("close_notes", "")
        session["resolution_code"] = data.get("close_code", "")
        session["resolved_by"] = data.get("resolved_by", "")
        
        # Notify the user via WebSocket that their issue is resolved
        resolution_message = data.get("close_notes", "Your issue has been resolved.")
        resolved_by = data.get("resolved_by", "IT Support")
        
        if escalation_id in active_connections:
            user_ws = active_connections[escalation_id].get("user")
            if user_ws:
                try:
                    await user_ws.send_json({
                        "type": "ticket_resolved",
                        "incident_number": incident_number,
                        "resolution_notes": resolution_message,
                        "resolved_by": resolved_by,
                        "close_code": data.get("close_code", "Solved")
                    })
                    await user_ws.send_json({"type": "session_closed"})
                except Exception as e:
                    print(f"Error notifying user: {e}")
        
        print(f"ServiceNow webhook: Incident {incident_number} resolved, escalation {escalation_id} closed")
        
        return {
            "status": "processed",
            "escalation_id": escalation_id,
            "action": "resolved"
        }
    else:
        # Other state changes (assigned, in progress, etc.) - just log
        print(f"ServiceNow webhook: Incident {incident_number} state changed to {state}")
        return {
            "status": "processed",
            "escalation_id": escalation_id,
            "action": "state_updated",
            "new_state": state
        }


@app.post("/api/escalation/create")
async def create_escalation_api(
    request: Request,
    user: User = Depends(get_current_user),
):
    """
    Create a new escalation session.
    Called internally by escalation tools.
    """
    data = await request.json()
    
    escalation_id = data.get("escalation_id") or f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    result = create_escalation_session(
        escalation_id=escalation_id,
        department=data.get("department", "IT_Support"),
        urgency=data.get("urgency", "normal"),
        issue_summary=data.get("issue_summary", ""),
        employee_id=data.get("employee_id", user.employee_id if user else "unknown"),
        user_session_id=data.get("session_id"),
        user_info={
            "employee_id": user.employee_id if user else "unknown",
            "email": user.email if user else None,
            "full_name": user.full_name if user else None,
            "department": user.department if user else None,
        } if user else None,
        servicenow_incident=data.get("servicenow_incident"),
    )
    
    return result


@app.post("/api/escalation/register")
async def register_escalation_session(request: Request):
    """
    Register an escalation session created by agent tools.
    Called internally - no authentication required.
    """
    data = await request.json()
    
    escalation_id = data.get("escalation_id")
    specialist_token = data.get("specialist_token")
    
    if not escalation_id or not specialist_token:
        return {"error": "Missing escalation_id or specialist_token"}
    
    # Determine if this is a ServiceNow-only session
    servicenow_only = data.get("servicenow_only", False)
    
    # Store session data
    session_data = {
        "escalation_id": escalation_id,
        "specialist_token": specialist_token,
        "department": data.get("department", "IT_Support"),
        "urgency": data.get("urgency", "normal"),
        "issue_summary": data.get("issue_summary", ""),
        "employee_id": data.get("employee_id", "unknown"),
        "servicenow_incident": data.get("servicenow_incident"),
        "servicenow_only": servicenow_only,
        "created_at": datetime.now().isoformat(),
        "status": "servicenow_only" if servicenow_only else "waiting_for_specialist",
        "specialist_joined": False,
        "specialist_name": None,
        "user_connected": False,
        "user_disconnected": False,
        "specialist_disconnected": False,
    }
    
    escalation_sessions[escalation_id] = session_data
    
    # Initialize chat history with appropriate message
    if servicenow_only:
        chat_histories[escalation_id] = [{
            "role": "system",
            "content": "ServiceNow ticket created. Responses will be handled via ServiceNow.",
            "timestamp": datetime.now().isoformat(),
        }]
    else:
        chat_histories[escalation_id] = [{
            "role": "system",
            "content": "Session created. Waiting for specialist to connect...",
            "timestamp": datetime.now().isoformat(),
        }]
    
    return {"status": "registered", "escalation_id": escalation_id, "servicenow_only": servicenow_only}


# =============================================================================
# Specialist WebSocket for Real-Time Chat
# =============================================================================

@app.websocket("/ws/specialist/{escalation_id}")
async def specialist_websocket(
    websocket: WebSocket,
    escalation_id: str,
    token: str = Query(...),
):
    """
    WebSocket endpoint for specialist real-time chat.
    Enables bidirectional communication between specialist and user.
    """
    # Validate token
    if not validate_specialist_token(escalation_id, token):
        await websocket.close(code=4001, reason="Invalid token")
        return
    
    # Check if session is already closed or resolved BEFORE accepting connection
    session = escalation_sessions.get(escalation_id)
    if session:
        session_status = session.get("status", "")
        if session_status in ("closed", "resolved"):
            await websocket.close(code=4002, reason=f"Session already ended ({session_status})")
            return
    
    await websocket.accept()
    
    # Register specialist connection
    if escalation_id not in active_connections:
        active_connections[escalation_id] = {}
    active_connections[escalation_id]["specialist"] = websocket
    
    # Update session
    if session:
        session["specialist_joined"] = True
        session["specialist_joined_at"] = datetime.now().isoformat()
        session["status"] = "specialist_connected"
        
        # Add system message to chat history
        chat_histories.setdefault(escalation_id, []).append({
            "role": "system",
            "content": "Specialist joined the chat",
            "timestamp": datetime.now().isoformat(),
        })
    
    # Notify user that specialist joined - important for waiting state
    user_ws = active_connections.get(escalation_id, {}).get("user")
    user_is_connected = False
    
    if user_ws:
        try:
            await user_ws.send_json({
                "type": "specialist_joined",
                "message": "A specialist has joined the chat and is ready to help you.",
                "specialist_name": session.get("specialist_name") if session else None
            })
            user_is_connected = True
        except Exception as e:
            print(f"Error notifying user of specialist join (user may be disconnected): {e}")
            # User WebSocket is stale, clean it up
            if escalation_id in active_connections:
                active_connections[escalation_id]["user"] = None
    
    # Always tell specialist about user's connection status
    if user_is_connected:
        await websocket.send_json({
            "type": "user_connected",
            "message": "User is online and ready to chat."
        })
    else:
        await websocket.send_json({
            "type": "waiting_for_user",
            "message": "Waiting for user to connect..."
        })
    
    try:
        while True:
            # Receive message from specialist
            data = await websocket.receive_json()
            
            if data.get("type") == "specialist_message":
                content = data.get("content", "")
                timestamp = datetime.now().isoformat()
                
                # Store in history
                chat_histories.setdefault(escalation_id, []).append({
                    "role": "specialist",
                    "content": content,
                    "timestamp": timestamp,
                })
                
                # Forward to user
                user_ws = active_connections.get(escalation_id, {}).get("user")
                if user_ws:
                    try:
                        await user_ws.send_json({
                            "type": "specialist_message",
                            "content": content,
                            "timestamp": timestamp,
                        })
                        print(f"[{escalation_id}] Specialist message forwarded to user: {content[:50]}...")
                    except Exception as e:
                        print(f"[{escalation_id}] Failed to forward to user: {e}")
                else:
                    print(f"[{escalation_id}] No user connected to receive specialist message")
                
                # Confirm to specialist
                await websocket.send_json({
                    "type": "message_sent",
                    "timestamp": timestamp,
                })
            
            elif data.get("type") == "specialist_joined":
                # Add system message to history
                chat_histories.setdefault(escalation_id, []).append({
                    "role": "system",
                    "content": "Specialist joined the chat",
                    "timestamp": datetime.now().isoformat(),
                })
            
            elif data.get("type") == "session_closed":
                # Notify user
                user_ws = active_connections.get(escalation_id, {}).get("user")
                if user_ws:
                    try:
                        await user_ws.send_json({"type": "session_closed"})
                    except:
                        pass
                break
    
    except WebSocketDisconnect:
        print(f"Specialist disconnected from {escalation_id}")
        # Update session status
        session = escalation_sessions.get(escalation_id)
        if session:
            session["specialist_disconnected"] = True
            session["specialist_disconnected_at"] = datetime.now().isoformat()
        
        # Notify user that specialist disconnected and close the session
        user_ws = active_connections.get(escalation_id, {}).get("user")
        if user_ws:
            try:
                await user_ws.send_json({
                    "type": "specialist_disconnected",
                    "message": "The specialist has disconnected from the chat."
                })
                await user_ws.send_json({"type": "session_closed"})
            except Exception as e:
                print(f"Error notifying user of specialist disconnect: {e}")
        
        # Add to chat history
        chat_histories.setdefault(escalation_id, []).append({
            "role": "system",
            "content": "Specialist disconnected from the chat",
            "timestamp": datetime.now().isoformat(),
        })
    finally:
        # Clean up connection
        if escalation_id in active_connections:
            active_connections[escalation_id]["specialist"] = None


@app.websocket("/ws/user/{escalation_id}")
async def user_escalation_websocket(websocket: WebSocket, escalation_id: str):
    """
    WebSocket endpoint for user during escalated chat.
    Allows user to continue chatting while waiting for/talking to specialist.
    """
    # Check if session exists and its status BEFORE accepting connection
    session = escalation_sessions.get(escalation_id)
    if not session:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "message": "Escalation session not found."
        })
        await websocket.close(code=4004, reason="Escalation not found")
        return
    
    # Check if session is already closed or resolved
    session_status = session.get("status", "")
    if session_status in ("closed", "resolved"):
        await websocket.accept()
        await websocket.send_json({
            "type": "session_closed",
            "message": f"This escalation session has ended (status: {session_status})."
        })
        await websocket.close(code=4003, reason=f"Session already ended ({session_status})")
        return
    
    await websocket.accept()
    print(f"[{escalation_id}] User WebSocket connected")
    
    # Check if this is a ServiceNow-only session
    if session.get("servicenow_only"):
        await websocket.send_json({
            "type": "servicenow_only",
            "message": "This ticket is being handled via ServiceNow. A specialist will respond through the ticketing system. Live chat is not available for this request.",
            "servicenow_incident": session.get("servicenow_incident")
        })
        await websocket.close(code=4002, reason="ServiceNow-only ticket - no live chat available")
        return
    
    # Register user connection
    if escalation_id not in active_connections:
        active_connections[escalation_id] = {}
    active_connections[escalation_id]["user"] = websocket
    
    # Update session status
    if session:
        session["user_connected"] = True
        session["user_connected_at"] = datetime.now().isoformat()
    
    # Send current status to user
    specialist_ws = active_connections.get(escalation_id, {}).get("specialist")
    if specialist_ws:
        # Specialist is already connected
        await websocket.send_json({
            "type": "specialist_joined",
            "message": "A specialist is connected and ready to assist you.",
            "specialist_name": session.get("specialist_name") if session else None
        })
        # Notify specialist that user connected
        try:
            await specialist_ws.send_json({
                "type": "user_connected",
                "message": "User is online"
            })
            print(f"[{escalation_id}] Notified specialist that user connected")
        except Exception as e:
            print(f"Error notifying specialist: {e}")
    else:
        # User is waiting for specialist
        await websocket.send_json({
            "type": "waiting_for_specialist",
            "message": "Waiting for a specialist to connect. You will be notified when they join."
        })
    
    try:
        while True:
            # Receive message from user
            data = await websocket.receive_json()
            
            if data.get("type") == "user_message":
                content = data.get("content", "")
                timestamp = datetime.now().isoformat()
                print(f"[{escalation_id}] User message received: {content[:50]}...")
                
                # Store in history
                chat_histories.setdefault(escalation_id, []).append({
                    "role": "user",
                    "content": content,
                    "timestamp": timestamp,
                })
                
                # Forward to specialist
                specialist_ws = active_connections.get(escalation_id, {}).get("specialist")
                if specialist_ws:
                    try:
                        await specialist_ws.send_json({
                            "type": "user_message",
                            "content": content,
                            "timestamp": timestamp,
                        })
                        print(f"[{escalation_id}] User message forwarded to specialist")
                    except Exception as e:
                        print(f"[{escalation_id}] Failed to forward to specialist: {e}")
                else:
                    print(f"[{escalation_id}] No specialist connected to receive user message")
            
            elif data.get("type") == "typing":
                # Forward typing indicator to specialist
                specialist_ws = active_connections.get(escalation_id, {}).get("specialist")
                if specialist_ws:
                    try:
                        await specialist_ws.send_json({"type": "user_typing"})
                    except:
                        pass
    
    except WebSocketDisconnect:
        print(f"User disconnected from escalation {escalation_id}")
        
        # Update session status
        session = escalation_sessions.get(escalation_id)
        if session:
            session["user_disconnected"] = True
            session["user_disconnected_at"] = datetime.now().isoformat()
        
        # Add to chat history
        chat_histories.setdefault(escalation_id, []).append({
            "role": "system",
            "content": "User disconnected from the chat",
            "timestamp": datetime.now().isoformat(),
        })
        
        # Notify specialist that user disconnected and end the session
        specialist_ws = active_connections.get(escalation_id, {}).get("specialist")
        if specialist_ws:
            try:
                await specialist_ws.send_json({
                    "type": "user_disconnected",
                    "message": "User has disconnected from the chat. The live chat session has ended."
                })
                await specialist_ws.send_json({"type": "session_closed"})
            except Exception as e:
                print(f"Error notifying specialist of user disconnect: {e}")
    finally:
        # Clean up
        if escalation_id in active_connections:
            active_connections[escalation_id]["user"] = None


# =============================================================================
# Helper function for escalation tools to use
# =============================================================================

def generate_specialist_session(
    escalation_id: str,
    department: str,
    urgency: str,
    issue_summary: str,
    employee_id: str,
    servicenow_incident: str = None,
) -> dict:
    """
    Generate a specialist session and return URLs.
    This function is called by escalation_tools.py
    """
    result = create_escalation_session(
        escalation_id=escalation_id,
        department=department,
        urgency=urgency,
        issue_summary=issue_summary,
        employee_id=employee_id,
        servicenow_incident=servicenow_incident,
    )
    
    return {
        "specialist_url": result["specialist_url"],
        "specialist_token": result["specialist_token"],
        "chat_url": f"{APP_BASE_URL}/escalation/{escalation_id}",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
