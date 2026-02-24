import json
import os
import uuid
import logging
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

# Import Agent and Service
from .agent import root_agent
from .github_service import GitHubService

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PR_Review_Server")

def validate_environment_variables():
    """
    Validates that all required environment variables are set and not empty.
    Exits the application if validation fails.
    """
    required_vars = {
        "GITHUB_TOKEN": "GitHub Personal Access Token",
        "GEMINI_MODEL": "Gemini Model Name"
    }
    
    # Check if using VertexAI or API Key
    use_vertexai = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper()
    
    if use_vertexai == "TRUE":
        required_vars["GOOGLE_CLOUD_PROJECT"] = "Google Cloud Project ID"
        logger.info("Using VertexAI mode")
    else:
        required_vars["GOOGLE_API_KEY"] = "Google API Key"
        logger.info("Using Google API Key mode")
    
    missing_vars = []
    empty_vars = []
    
    for var_name, var_description in required_vars.items():
        var_value = os.getenv(var_name)
        
        if var_value is None:
            missing_vars.append(f"{var_name} ({var_description})")
        elif not var_value.strip():
            empty_vars.append(f"{var_name} ({var_description})")
    
    if missing_vars or empty_vars:
        error_msg = "❌ Environment variable validation failed:\n"
        
        if missing_vars:
            error_msg += "\n  Missing variables:\n"
            for var in missing_vars:
                error_msg += f"    - {var}\n"
        
        if empty_vars:
            error_msg += "\n  Empty variables:\n"
            for var in empty_vars:
                error_msg += f"    - {var}\n"
        
        error_msg += "\nPlease create a .env file based on .env.example and set all required values."
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    logger.info("✅ All required environment variables are set")

# Validate environment before initializing services
validate_environment_variables()

app = FastAPI(title="AI PR Code Reviewer Webhook")

# Services
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, app_name="pr_reviewer", session_service=session_service)
gh_service = GitHubService()

class WebhookPayload(BaseModel):
    # Simplified model, we'll parse raw dict usually for webhooks
    pass

async def process_pr_review(repo_name: str, pr_number: int, commit_sha: str, language: str = "python"):
    """
    Background task to run the review so GitHub webhook doesn't timeout.
    """
    try:
        logger.info(f"🔍 Starting review for {repo_name} PR #{pr_number}")
        
        # 1. Fetch PR Metadata
        logger.info(f"📋 Fetching PR metadata...")
        pr_metadata = gh_service.get_pr_metadata(repo_name, pr_number)
        
        # 2. Fetch Diff
        logger.info(f"📥 Fetching PR diff...")
        diff_text = gh_service.get_pr_diff(repo_name, pr_number)
        
        if not diff_text or "Error" in diff_text:
            logger.error(f"❌ Failed to fetch diff: {diff_text}")
            return

        diff_lines = len(diff_text.split('\n'))
        diff_size = len(diff_text)
        logger.info(f"📊 Diff received: {diff_lines} lines, {diff_size} bytes")

        # 4. Construct Agent Input
        # Using a session ID per PR ensures isolation
        session_id = f"{repo_name.replace('/', '_')}_{pr_number}_{uuid.uuid4().hex[:6]}"
        user_id = "github_webhook"
        
        await session_service.create_session(app_name="pr_reviewer", user_id=user_id, session_id=session_id)
        
        agent_input = {
            "repo": repo_name,
            "pr_number": pr_number,
            "language": language, # In a real app, detect this file by file or from repo stats
            "diff": diff_text[:50000] # Truncate if huge to fit context
        }
        
        if diff_size > 50000:
            logger.warning(f"⚠️  Diff truncated from {diff_size} to 50000 bytes")
        
        message = types.Content(role="user", parts=[types.Part(text=json.dumps(agent_input))])

        # 5. Run Agent
        logger.info(f"🤖 Running AI agent review...")
        final_json_str = ""
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
            if event.is_final_response() and event.content:
                final_json_str = event.content.parts[0].text

        # 6. Parse Decision
        # Cleanup output (sometimes models wrap in ```json ```)
        logger.info(f"📋 Parsing AI review response...")
        cleaned = final_json_str.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
        result = json.loads(cleaned.strip())
        
        decision = result.get("decision", "COMMENT")
        summary = result.get("summary_markdown", "No summary provided.")
        checks = result.get("checks", {})

        logger.info(f"✅ Review completed with decision: {decision}")
        logger.info(f"📊 Checks performed: {', '.join(checks.keys())}")

        # 7. Post Comment
        logger.info(f"💬 Posting review comment on PR #{pr_number}...")
        comment_header = f"## 🤖 AI Code Review: {decision}\n\n"
        gh_service.post_comment(repo_name, pr_number, comment_header + summary)
        
        logger.info(f"🎉 Completed review for {repo_name} PR #{pr_number} - Decision: {decision}")

    except Exception as e:
        logger.error(f"❌ Error in processing PR: {e}")

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives GitHub Pull Request events.
    """
    try:
        payload = await request.json()
        
        event_type = request.headers.get("X-GitHub-Event")
        logger.info(f"📥 Received GitHub Event: {event_type}")
        
        if event_type != "pull_request":
            logger.info(f"⏭️  Ignored non-PR event: {event_type}")
            return {"message": "Ignored non-PR event"}
            
        action = payload.get("action")
        if action not in ["opened", "synchronize", "reopened"]:
            logger.info(f"⏭️  Ignored PR action: {action}")
            return {"message": f"Ignored PR action: {action}"}

        # Extract Details
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        sender = payload.get("sender", {})
        
        repo_name = repo.get("full_name")
        pr_number = pr.get("number")
        commit_sha = pr.get("head", {}).get("sha")
        pr_title = pr.get("title")
        pr_author = pr.get("user", {}).get("login")
        pr_url = pr.get("html_url")
        base_branch = pr.get("base", {}).get("ref")
        head_branch = pr.get("head", {}).get("ref")
        
        if not repo_name or not pr_number:
            raise HTTPException(status_code=400, detail="Invalid Payload")

        # Log PR details
        logger.info("=" * 80)
        logger.info(f"🔔 Pull Request {action.upper()}")
        logger.info(f"📦 Repository: {repo_name}")
        logger.info(f"🔢 PR Number: #{pr_number}")
        logger.info(f"📝 Title: {pr_title}")
        logger.info(f"👤 Author: {pr_author}")
        logger.info(f"🌿 Branches: {head_branch} → {base_branch}")
        logger.info(f"🔗 URL: {pr_url}")
        logger.info(f"📌 Commit SHA: {commit_sha[:8]}...")
        logger.info(f"🚀 Triggered by: {sender.get('login')}")
        logger.info("=" * 80)

        # Hand off to background task
        background_tasks.add_task(process_pr_review, repo_name, pr_number, commit_sha)
        
        return {"message": "Review queued"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
