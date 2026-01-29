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
        logger.info(f"Starting review for {repo_name} PR #{pr_number}")
        
        # 1. Update Status to Pending
        gh_service.set_status_check(repo_name, commit_sha, "pending", "AI Agents are reviewing code...", "security")
        gh_service.set_status_check(repo_name, commit_sha, "pending", "AI Agents are reviewing code...", "logic")

        # 2. Fetch Diff
        diff_text = gh_service.get_pr_diff(repo_name, pr_number)
        
        if not diff_text or "Error" in diff_text:
            logger.error("Failed to fetch diff")
            return

        # 3. Construct Agent Input
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
        
        message = types.Content(role="user", parts=[types.Part(text=json.dumps(agent_input))])

        # 4. Run Agent
        final_json_str = ""
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
            if event.is_final_response() and event.content:
                final_json_str = event.content.parts[0].text

        # 5. Parse Decision
        # Cleanup output (sometimes models wrap in ```json ```)
        cleaned = final_json_str.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
            
        result = json.loads(cleaned.strip())
        
        decision = result.get("decision", "COMMENT")
        summary = result.get("summary_markdown", "No summary provided.")
        checks = result.get("checks", {})

        # 6. Post Comment
        comment_header = f"## 🤖 AI Code Review: {decision}\n\n"
        gh_service.post_comment(repo_name, pr_number, comment_header + summary)

        # 7. Update Status Checks
        for check_name, check_status in checks.items():
            state = "success" if check_status == "success" else "failure"
            desc = f"{check_name.capitalize()} check {state}."
            gh_service.set_status_check(repo_name, commit_sha, state, desc, check_name)

        # 8. Final Decision Check
        final_state = "success" if decision == "APPROVE" else "failure"
        gh_service.set_status_check(repo_name, commit_sha, final_state, f"Overall Decision: {decision}", "overall-decision")
        
        logger.info(f"Completed review for {repo_name} PR #{pr_number}")

    except Exception as e:
        logger.error(f"Error in processing PR: {e}")
        gh_service.set_status_check(repo_name, commit_sha, "error", "Internal Agent Error", "overall-decision")

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives GitHub Pull Request events.
    """
    try:
        payload = await request.json()
        
        event_type = request.headers.get("X-GitHub-Event")
        if event_type != "pull_request":
            return {"message": "Ignored non-PR event"}
            
        action = payload.get("action")
        if action not in ["opened", "synchronize", "reopened"]:
            return {"message": f"Ignored PR action: {action}"}

        # Extract Details
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        
        repo_name = repo.get("full_name")
        pr_number = pr.get("number")
        commit_sha = pr.get("head", {}).get("sha")
        
        if not repo_name or not pr_number:
            raise HTTPException(status_code=400, detail="Invalid Payload")

        # Hand off to background task
        background_tasks.add_task(process_pr_review, repo_name, pr_number, commit_sha)
        
        return {"message": "Review queued"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "ok"}
