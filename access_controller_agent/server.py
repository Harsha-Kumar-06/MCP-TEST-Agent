"""
FastAPI server for the Access Controller agent. 
Automatically polls email inbox every 30 seconds and processes incoming requests.
"""
import os
import uuid
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .agent import root_agent
from .email_service import get_email_service

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AccessController")

# Configuration
EMAIL_POLL_INTERVAL = int(os.getenv("EMAIL_POLL_INTERVAL", "30"))  # seconds
EMAIL_POLL_ENABLED = os.getenv("EMAIL_POLL_ENABLED", "true").lower() == "true"

session_service = InMemorySessionService()
runner = None  # Will be initialized in lifespan


async def run_agent(message: str, session_id: Optional[str] = None) -> str:
    """
    Run the agent with a message and return the final response.
    """
    if session_id is None:
        session_id = str(uuid.uuid4())
    user_id = "api_user"

    await session_service.create_session(
        app_name="access_controller",
        user_id=user_id,
        session_id=session_id,
    )

    agent_message = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=agent_message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    return final_text.strip() if final_text else "No response generated."


# Keywords that indicate an access-related request
ACCESS_REQUEST_KEYWORDS = [
    'access', 'grant', 'revoke', 'remove', 'add', 'permission', 
    'jira', 'project', 'role', 'developer', 'admin', 'administrator',
    'onboard', 'offboard', 'invite', 'user', 'member', 'team'
]

# Domains/senders to always ignore (newsletters, marketing, etc.)
IGNORE_SENDERS = [
    'noreply@', 'no-reply@', 'newsletter@', 'marketing@', 'info@',
    'notifications@', 'updates@', 'news@', 'promo@', 'support@'
]


def is_access_request(email_data: dict) -> bool:
    """
    Determine if an email looks like a legitimate access request.
    Returns True if it should be processed, False if it should be skipped.
    """
    from_email = email_data.get('from_email', email_data.get('from', '')).lower()
    subject = email_data.get('subject', '').lower()
    body = email_data.get('body', '').lower()
    
    # Skip emails from ignored senders (newsletters, marketing, etc.)
    for ignore in IGNORE_SENDERS:
        if ignore in from_email:
            return False
    
    # Check if subject or body contains access-related keywords
    content = f"{subject} {body}"
    for keyword in ACCESS_REQUEST_KEYWORDS:
        if keyword in content:
            return True
    
    # Default: skip if no keywords found
    return False


async def process_single_email(email_data: dict) -> dict:
    """
    Process a single UNREAD email through the agent.
    The agent will:
    1. Parse the request
    2. Execute the action (if all info is available) OR ask for more info
    3. Send a reply email with the result or follow-up question
    """
    email_svc = get_email_service()
    
    from_email = email_data.get('from_email', email_data.get('from', 'Unknown'))
    subject = email_data.get('subject', 'No Subject')
    message_id = email_data.get('message_id', '')
    in_reply_to = email_data.get('in_reply_to', '')
    references = email_data.get('references', '')
    
    # Check if this is a reply to a previous thread (follow-up from user)
    is_followup = bool(in_reply_to or references)
    
    try:
        email_message = f"""
Process this incoming email request:

=== EMAIL DETAILS ===
From: {from_email}
Subject: {subject}
Date: {email_data.get('date', 'Unknown')}
Email ID: {email_data.get('id', 'Unknown')}
Message-ID: {message_id}
Is Follow-up Reply: {is_followup}

=== EMAIL BODY ===
{email_data.get('body', '')}

=== YOUR TASK ===
1. Parse this email to understand what the user is requesting
2. Execute the appropriate action by delegating to the right sub-agent(s) (JiraAgent, ConfluenceAgent, BitbucketAgent)
3. After the action completes (or if you need more information), you MUST send a reply email using EmailAgent

IMPORTANT RULES FOR EMAIL THREADING:
- ALWAYS send a reply email to {from_email} when done
- CRITICAL: Pass the Email ID ({email_data.get('id', 'Unknown')}) to EmailAgent so it can use email_reply to maintain the thread
- This ensures your reply appears in the same conversation thread in the user's email client
- If the action was successful: Send a confirmation email with details of what was done
- If more information is needed: Send a follow-up email asking for the specific missing details  
- If there was an error: Send an email explaining the issue
- Keep the reply professional and concise

Example transfer to EmailAgent:
"Transfer to EmailAgent to send reply. Original Email ID: {email_data.get('id', 'Unknown')}. Recipient: {from_email}. Message: [your message here]"
"""
        response = await run_agent(email_message)
        
        # Mark as read AFTER successful processing
        email_svc.mark_as_read(email_data.get('id'))
        
        logger.info(f"Agent response: {response[:200]}..." if len(response) > 200 else f"Agent response: {response}")
        
        return {
            "email_id": email_data.get('id'),
            "from": from_email,
            "subject": subject,
            "status": "processed",
            "response": response
        }
    except Exception as e:
        logger.exception("Failed to process email %s: %s", email_data.get('id'), e)
        
        # Try to send an error notification email with threading
        try:
            email_id = email_data.get('id')
            if email_id:
                # Use email_reply to maintain thread
                from .tools import email_reply
                email_reply(
                    original_email_id=email_id,
                    reply_body=f"""Hi,

We encountered an error processing your request. Please try again or contact support.

Error: {str(e)}

Best regards,
Access Controller Bot""",
                    include_original=False
                )
            else:
                # Fallback to send_email if no email ID
                email_svc.send_email(
                    to=from_email,
                    subject=f"Re: {subject}",
                    body=f"""Hi,

We encountered an error processing your request. Please try again or contact support.

Error: {str(e)}

Best regards,
Access Controller Bot"""
                )
            # Still mark as read to avoid reprocessing
            email_svc.mark_as_read(email_data.get('id'))
        except:
            pass
        
        return {
            "email_id": email_data.get('id'),
            "from": from_email,
            "subject": subject,
            "status": "error",
            "error": str(e)
        }


async def email_polling_task():
    """Background task that polls for new UNREAD emails every EMAIL_POLL_INTERVAL seconds."""
    logger.info(f"📧 Email polling started (interval: {EMAIL_POLL_INTERVAL}s)")
    
    while True:
        try:
            await asyncio.sleep(EMAIL_POLL_INTERVAL)
            
            email_svc = get_email_service()
            unread = email_svc.fetch_unread_emails(limit=10)
            
            if unread.get("status") != "success":
                logger.warning(f"Failed to fetch emails: {unread.get('error')}")
                continue
            
            emails = unread.get("emails", [])
            
            if emails:
                logger.info(f"📬 Found {len(emails)} unread email(s), checking for access requests...")
                
                for email_data in emails:
                    # Filter: Only process emails that look like access requests
                    if not is_access_request(email_data):
                        logger.info(f"  ⏭️  Skipping (not an access request): {email_data.get('subject')} from {email_data.get('from_email', email_data.get('from'))}")
                        continue
                    
                    logger.info(f"  📧 Processing access request: {email_data.get('subject')} from {email_data.get('from_email', email_data.get('from'))}")
                    result = await process_single_email(email_data)
                    
                    if result.get("status") == "processed":
                        logger.info(f"  ✅ Processed successfully")
                    else:
                        logger.error(f"  ❌ Failed: {result.get('error')}")
            
        except asyncio.CancelledError:
            logger.info("📧 Email polling stopped")
            break
        except Exception as e:
            logger.exception(f"Error in email polling task: {e}")
            # Continue polling despite errors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    global runner
    
    # Startup
    logger.info("🚀 Starting Access Controller Agent Server...")
    
    runner = Runner(
        agent=root_agent,
        app_name="access_controller",
        session_service=session_service,
    )
    
    # Start email polling background task if enabled
    polling_task = None
    if EMAIL_POLL_ENABLED:
        polling_task = asyncio.create_task(email_polling_task())
        logger.info(f"📧 Email auto-polling enabled (every {EMAIL_POLL_INTERVAL}s)")
    else:
        logger.info("📧 Email auto-polling disabled (set EMAIL_POLL_ENABLED=true to enable)")
    
    logger.info("✅ Server ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
    logger.info("👋 Goodbye!")


app = FastAPI(title="Access Controller Agent", lifespan=lifespan)


class AccessRequest(BaseModel):
    """Incoming message (e.g. email body or direct request)."""
    message: str


class AccessResponse(BaseModel):
    """Agent response text."""
    response: str


class EmailPollRequest(BaseModel):
    """Request to poll and process emails."""
    limit: Optional[int] = 5
    auto_process: Optional[bool] = True


class EmailPollResponse(BaseModel):
    """Response from email polling."""
    emails_found: int
    processed: int
    results: list


@app.post("/request", response_model=AccessResponse)
async def handle_request(req: AccessRequest):
    """
    Handle an access request (e.g. "Grant john@company.com access to project PROJ on Jira").
    Use a new session per request for isolation.
    """
    try:
        response = await run_agent(req.message)
        return AccessResponse(response=response)
    except Exception as e:
        logger.exception("Agent run failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/access", response_model=AccessResponse)
async def handle_access(req: AccessRequest):
    """Alias for /request for semantic clarity."""
    return await handle_request(req)


@app.post("/email/poll", response_model=EmailPollResponse)
async def poll_emails(req: EmailPollRequest):
    """
    Manually poll for new unread emails and optionally process them through the agent.
    Note: Auto-polling runs every 30 seconds in the background.
    """
    try:
        email_svc = get_email_service()
        unread = email_svc.fetch_unread_emails(limit=req.limit)
        
        if unread.get("status") != "success":
            raise HTTPException(status_code=500, detail=unread.get("error", "Failed to fetch emails"))
        
        emails = unread.get("emails", [])
        results = []
        
        if req.auto_process and emails:
            for email_data in emails:
                result = await process_single_email(email_data)
                results.append(result)
        else:
            # Just return the email list without processing
            for email_data in emails:
                results.append({
                    "email_id": email_data.get('id'),
                    "from": email_data.get('from'),
                    "subject": email_data.get('subject'),
                    "status": "pending"
                })
        
        return EmailPollResponse(
            emails_found=len(emails),
            processed=len([r for r in results if r.get('status') == 'processed']),
            results=results
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Email poll failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email/unread")
async def get_unread_emails(limit: int = 10):
    """
    Get list of unread emails without processing them.
    Useful for checking what's in the inbox.
    """
    try:
        email_svc = get_email_service()
        result = email_svc.fetch_unread_emails(limit=limit)
        return result
    except Exception as e:
        logger.exception("Failed to fetch unread emails: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/email/status")
def email_status():
    """Check the status of email polling."""
    return {
        "polling_enabled": EMAIL_POLL_ENABLED,
        "poll_interval_seconds": EMAIL_POLL_INTERVAL,
    }


@app.get("/health")
def health():
    return {"status": "ok"}

