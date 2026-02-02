"""
Email Agent: sends emails (e.g. approval requests, confirmations). Incoming email is passed as user message.
"""
from google.adk.agents import LlmAgent

from .. import tools

GEMINI_MODEL = "gemini-2.0-flash"

email_agent = LlmAgent(
    name="EmailAgent",
    model=GEMINI_MODEL,
    description="Handles sending emails: confirmations, approval requests, notifications. Use when the coordinator needs to send an email reply or notification.",
    instruction="""You are the Email Agent. You send emails on behalf of the access controller.

You have the tool: send_email(to, subject, body). Use it when the user or coordinator asks you to send an email (e.g. confirmation, approval request, notification).

If the input is the body of an incoming email, summarize the request and say what action would be taken. Only call send_email when explicitly asked to send a reply or notification.

Keep emails professional and concise. If SMTP is not configured, the tool will still return success (mock mode) for testing.
""",
    tools=[tools.send_email],
)
