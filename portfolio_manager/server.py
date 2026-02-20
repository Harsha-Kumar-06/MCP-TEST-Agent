"""
Portfolio Manager - FastAPI Server

This module provides the REST API and web interface for the portfolio manager.
It integrates Google ADK with FastAPI for serving the multi-agent system.

Usage:
    uvicorn portfolio_manager.server:app --reload --port 8001
"""

# Python 3.9 compatibility patch for Google ADK
import sys
import types

if sys.version_info < (3, 10):
    if not hasattr(types, 'UnionType'):
        types.UnionType = type(None)

import os
import re
import json
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dotenv import load_dotenv

# Load environment variables
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

if not os.environ.get("GOOGLE_API_KEY"):
    print("WARNING: GOOGLE_API_KEY not found in environment variables!")

# Google ADK imports
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

# Import the portfolio agent (use root_agent directly with autonomous prompt)
from portfolio_manager.agent import root_agent

# Import A2A models
from .a2a_models import (
    AgentCard, AgentInterface, AgentProvider, AgentCapability,
    Message, Task, TaskStatus, Artifact, Part, SendMessageRequest
)
from datetime import datetime
import uuid

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
DATA_DIR = os.path.join(BASE_DIR, "data")

# FastAPI app
app = FastAPI(
    title="Automated Portfolio Manager",
    description="AI-powered investment portfolio manager using Google ADK agents",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")


@app.get("/.well-known/agent-card.json", response_model=AgentCard)
async def get_agent_card():
    """Returns the A2A Agent Card for discovery."""
    return AgentCard(
        name="Portfolio Manager",
        description="Autonomous AI agent for personalized investment portfolio creation and analysis.",
        version="2.0.0",
        supportedInterfaces=[
            AgentInterface(
                url="/message:send",
                protocolBinding="HTTP+JSON",
                protocolVersion="0.3"
            )
        ],
        provider=AgentProvider(
            organization="Drayvn",
            url="https://drayvn.ai"
        ),
        capabilities=AgentCapability(
            streaming=False,
            pushNotifications=False,
            extensions=[]
        ),
        defaultInputModes=["text/plain"],
        defaultOutputModes=["application/json", "text/markdown"]
    )


# Request/Response Models
class PortfolioRequest(BaseModel):
    """Request model for portfolio generation."""
    capital: float = Field(..., description="Investment capital", ge=100)
    goal: str = Field(default="balanced_growth", description="Investment goal")
    horizon: str = Field(default="3_5_years", description="Time horizon")
    max_loss: int = Field(default=15, description="Maximum acceptable loss %", ge=5, le=50)
    experience: str = Field(default="intermediate", description="Investment experience")
    income_stability: str = Field(default="stable", description="Income stability")


class PortfolioResponse(BaseModel):
    """Response model with agent-generated data."""
    success: bool
    error: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    macro_outlook: Optional[Dict[str, Any]] = None
    top_sectors: Optional[Dict[str, Any]] = None
    selected_stocks: Optional[Dict[str, Any]] = None
    portfolio: Optional[Dict[str, Any]] = None
    performance_report: Optional[Dict[str, Any]] = None
    backtest_results: Optional[Dict[str, Any]] = None
    final_report: Optional[str] = None
    raw_response: Optional[str] = None


def calculate_risk_score(goal: str, max_loss: int, experience: str, horizon: str) -> Dict[str, Any]:
    """Calculate risk profile from user inputs."""
    goal_scores = {
        "preserve_capital": 2,
        "income": 4,
        "balanced_growth": 6,
        "aggressive_growth": 8
    }
    
    horizon_scores = {
        "less_than_1_year": 2,
        "1_3_years": 4,
        "3_5_years": 6,
        "5_10_years": 8,
        "10_plus_years": 9
    }
    
    exp_scores = {
        "none": 2,
        "beginner": 4,
        "intermediate": 6,
        "advanced": 8,
        "expert": 10
    }
    
    goal_score = goal_scores.get(goal, 5)
    horizon_score = horizon_scores.get(horizon, 5)
    loss_score = min(max_loss / 5, 6)  # 5%→1, 30%→6
    exp_score = exp_scores.get(experience, 5)
    
    avg_score = (goal_score + horizon_score + loss_score + exp_score) / 4
    risk_score = max(1, min(10, round(avg_score)))
    
    categories = [
        "Ultra Conservative", "Very Conservative", "Conservative",
        "Moderately Conservative", "Moderate", "Moderately Aggressive",
        "Growth", "Aggressive", "Very Aggressive", "Maximum Risk"
    ]
    
    return {
        "risk_score": risk_score,
        "risk_category": categories[risk_score - 1],
        "goal_score": goal_score,
        "horizon_score": horizon_score,
        "experience_score": exp_score
    }


def extract_agent_outputs(response_text: str) -> Dict[str, Any]:
    """Parse all structured JSON outputs from agent response."""
    outputs = {}
    
    # Find all JSON blocks in code fences
    json_pattern = r'```json\s*(\{[\s\S]*?\})\s*```'
    matches = re.findall(json_pattern, response_text, re.DOTALL)
    
    # Key mapping: what the agent outputs -> what the UI expects
    key_mapping = {
        "macro_outlook": "macro_outlook",
        "top_sectors": "top_sectors",
        "selected_stocks": "selected_stocks",
        "portfolio": "portfolio",
        "performance_report": "performance_report", 
        "backtest_results": "backtest_results"
    }
    
    for match in matches:
        try:
            parsed = json.loads(match)
            # The agent wraps outputs like {"macro_outlook": {...}}
            # Extract the inner content
            for agent_key, output_key in key_mapping.items():
                if agent_key in parsed:
                    outputs[output_key] = parsed[agent_key]
                    break
        except json.JSONDecodeError:
            continue
    
    return outputs


async def run_autonomous_agent(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the portfolio agent pipeline with the given profile.
    Uses root_agent with multi-turn interaction to trigger the analysis pipeline.
    """
    # Create runner with root_agent
    runner = InMemoryRunner(agent=root_agent, app_name="portfolio_manager")
    
    # Create session
    session = await runner.session_service.create_session(
        app_name="portfolio_manager",
        user_id="web_user"
    )
    
    # Build profile JSON for agent
    profile_json = json.dumps({"user_profile": profile}, indent=2)
    
    # First message: provide the complete profile
    message1 = genai_types.Content(
        role="user",
        parts=[genai_types.Part.from_text(text=f"""I have already collected my complete investor profile. Here it is:

{profile_json}

I am ready to see my portfolio. Please proceed with the complete analysis pipeline and generate my personalized portfolio now. I confirm I want to proceed.""")]
    )
    
    # Collect responses from first message
    collected_responses = []
    
    try:
        async for event in runner.run_async(
            user_id="web_user",
            session_id=session.id,
            new_message=message1
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        collected_responses.append(part.text)
    except Exception as e:
        print(f"First message error: {e}")
    
    # Check if the agent is asking for confirmation
    first_response = "\n".join(collected_responses)
    
    # If response is short or asking for confirmation, send follow-up
    if len(first_response) < 1000 or "confirm" in first_response.lower() or "ready" in first_response.lower():
        # Second message: explicit confirmation to start pipeline
        message2 = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text="""Yes, please proceed immediately. Generate my portfolio now. Transfer to the analysis_pipeline and run all sub-agents:
1. macro_agent for market analysis
2. sector_agent for sector selection
3. stock_selection_agent for stock picks
4. portfolio_construction_agent for allocation
5. performance_agent for metrics
6. backtest_agent for validation
7. report_synthesizer_agent for the final report

Start the analysis now.""")]
        )
        
        try:
            async for event in runner.run_async(
                user_id="web_user",
                session_id=session.id,
                new_message=message2
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            collected_responses.append(part.text)
        except Exception as e:
            print(f"Second message error: {e}")
    
    # Combine all responses
    full_response = "\n\n".join(collected_responses)
    
    # Parse structured outputs
    parsed_outputs = extract_agent_outputs(full_response)
    
    return {
        "raw_response": full_response,
        "parsed": parsed_outputs,
        "session_id": session.id
    }


# Store active sessions for A2A
_a2a_runners: Dict[str, InMemoryRunner] = {}
_a2a_sessions: Dict[str, Any] = {}

async def get_or_create_runner_session(context_id: str):
    """Get or create a runner and session for a given context ID."""
    if context_id not in _a2a_runners:
        runner = InMemoryRunner(agent=root_agent, app_name="portfolio_manager")
        _a2a_runners[context_id] = runner
        try:
            # Create session using the runner's session service
            session = await runner.session_service.create_session(
                app_name="portfolio_manager",
                user_id=f"a2a_user_{context_id}"
            )
            _a2a_sessions[context_id] = session
        except Exception as e:
            # Fallback for older ADK versions or different runner implementations
            print(f"Session creation warning: {e}")
            _a2a_sessions[context_id] = type('obj', (object,), {'id': context_id})
            
    return _a2a_runners[context_id], _a2a_sessions[context_id]


@app.post("/message:send", response_model=Dict[str, Any])
async def a2a_send_message(request: SendMessageRequest):
    """
    A2A Protocol endpoint for sending messages to the agent.
    Supports multi-turn conversation for portfolio creation.
    """
    try:
        # Use contextId to maintain conversation state
        context_id = request.contextId or request.conversationId or str(uuid.uuid4())
        
        # Get runner and session
        runner, session = await get_or_create_runner_session(context_id)
        
        # Extract user text from message parts
        user_text = ""
        if request.message.parts:
            for part in request.message.parts:
                if part.text:
                    user_text += part.text + " "
        
        if not user_text.strip():
            raise HTTPException(status_code=400, detail="Message text is empty")

        # Create message for ADK runner
        adk_message = genai_types.Content(
            role="user",
            parts=[genai_types.Part.from_text(text=user_text)]
        )
        
        # Run agent turn
        agent_response_text = ""
        artifacts = []
        
        try:
            # Collect response parts
            async for event in runner.run_async(
                user_id=f"a2a_user_{context_id}",
                session_id=session.id,
                new_message=adk_message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            agent_response_text += part.text
        except Exception as e:
            print(f"Agent execution error: {e}")
            agent_response_text = f"I encountered an error processing your request: {str(e)}"

        # Check for structured artifacts in the response (JSON blocks)
        # The agent outputs JSON for the final portfolio
        parsed_outputs = extract_agent_outputs(agent_response_text)
        
        if parsed_outputs:
            # If we have structured data, create artifacts
            for key, data in parsed_outputs.items():
                artifacts.append(Artifact(
                    artifactId=str(uuid.uuid4()),
                    name=key.replace("_", " ").title(),
                    parts=[Part(
                        text=json.dumps(data, indent=2),
                        mediaType="application/json"
                    )]
                ))

        # Generate unique Task ID for this interaction
        task_id = str(uuid.uuid4())
        
        # Determine status
        # If we have a full portfolio (all keys present), it's completed
        # Otherwise it's likely waiting for more input
        is_complete = "portfolio" in parsed_outputs
        
        response_status = TaskStatus(
            state="completed" if is_complete else "input_required",
            message=Message(
                messageId=str(uuid.uuid4()),
                role="ROLE_AGENT",
                parts=[Part(text=agent_response_text)],
                contextId=context_id,
                taskId=task_id,
                created=datetime.utcnow()
            ),
            timestamp=datetime.utcnow()
        )
        
        # Construct Task object
        task = Task(
            id=task_id,
            contextId=context_id,
            status=response_status,
            artifacts=artifacts if artifacts else None
        )
        
        return {"task": task.dict()}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-portfolio", response_model=PortfolioResponse)
async def generate_portfolio(request: PortfolioRequest):
    """
    Generate portfolio using the autonomous AI agent pipeline.
    
    The agent will:
    1. Analyze macroeconomic conditions
    2. Select optimal sectors
    3. Pick quality stocks
    4. Construct diversified portfolio
    5. Calculate performance metrics
    6. Run historical backtests
    7. Generate investment report
    """
    try:
        # Calculate risk profile
        risk_data = calculate_risk_score(
            request.goal, 
            request.max_loss, 
            request.experience,
            request.horizon
        )
        
        # Build complete profile for agent
        profile = {
            "capital": request.capital,
            "currency": "USD",
            "investment_goal": request.goal,
            "time_horizon": request.horizon,
            "time_horizon_years": {
                "less_than_1_year": 0.5,
                "1_3_years": 2,
                "3_5_years": 4,
                "5_10_years": 7,
                "10_plus_years": 15
            }.get(request.horizon, 5),
            "risk_tolerance": request.max_loss,
            "max_loss_percent": request.max_loss,
            "investment_experience": request.experience,
            "income_stability": request.income_stability,
            "risk_score": risk_data["risk_score"],
            "risk_category": risk_data["risk_category"]
        }
        
        # Run agent pipeline
        result = await run_autonomous_agent(profile)
        
        raw_response = result.get("raw_response", "")
        parsed = result.get("parsed", {})
        
        # Build response
        return PortfolioResponse(
            success=True,
            profile=profile,
            macro_outlook=parsed.get("macro_outlook"),
            top_sectors=parsed.get("top_sectors"),
            selected_stocks=parsed.get("selected_stocks"),
            portfolio=parsed.get("portfolio"),
            performance_report=parsed.get("performance_report"),
            backtest_results=parsed.get("backtest_results"),
            final_report=raw_response if len(raw_response) > 500 else None,
            raw_response=raw_response
        )
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error: {error_msg}")
        return PortfolioResponse(
            success=False,
            error=str(e)
        )


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI page."""
    html_path = os.path.join(UI_DIR, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
        <body>
            <h1>Portfolio Manager</h1>
            <p>UI files not found. Please ensure the ui/ folder exists.</p>
            <p>API documentation available at <a href="/docs">/docs</a></p>
        </body>
        </html>
        """)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "portfolio_manager",
        "version": "2.0.0",
        "agent": "autonomous_agent"
    }


@app.get("/api/info")
async def api_info():
    """Get API and agent information."""
    return {
        "name": "Automated Portfolio Manager",
        "version": "2.0.0",
        "agent_type": "autonomous",
        "pipeline": [
            "macro_agent - Macroeconomic Analysis",
            "sector_agent - Sector Selection",
            "stock_selection_agent - Stock Analysis",
            "portfolio_construction_agent - Capital Allocation",
            "performance_agent - Metrics Calculation",
            "backtest_agent - Historical Validation",
            "report_synthesizer_agent - Report Generation"
        ],
        "endpoints": [
            {"method": "POST", "path": "/api/generate-portfolio", "description": "Generate portfolio via AI agents"},
            {"method": "GET", "path": "/health", "description": "Health check"},
            {"method": "GET", "path": "/docs", "description": "API documentation"}
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
