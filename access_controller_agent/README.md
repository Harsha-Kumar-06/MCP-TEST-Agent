# Access Controller Agent

AI-powered organizational access authority agent built with **Google ADK**. It acts as a central, automated system for managing user access to various systems (currently **Jira**, with planned support for Bitbucket, GitHub, Teams, etc.).

## Primary Interface: Email

**Email is the main entry point** for interacting with this agent. Users send emails requesting access changes, and the agent:
1. Reads incoming emails from Gmail
2. Parses the request to understand the intent
3. Executes the appropriate action (grant/revoke access, etc.)
4. Sends a reply with the result
5. Asks follow-up questions if more information is needed

## Architecture (Hierarchical, ADK)

- **Root:** `AccessControllerCoordinator` (LlmAgent) – routes requests to specialists via LLM-driven delegation.
- **Sub-agents:**
  - **JiraAgent** – Jira project access: grant, revoke, list user access, look up user by email, invite new users. Uses Jira Cloud REST API v3.
  - **EmailAgent** – Reads and processes incoming emails, sends replies, follow-ups, and notifications. Uses Gmail IMAP/SMTP.

**Flow:** 
1. Email arrives → Agent fetches unread emails
2. Coordinator parses intent → Delegates to **JiraAgent** for access operations
3. JiraAgent executes the action → Returns result
4. Coordinator → Delegates to **EmailAgent** to send reply

## Capabilities

### Jira Access Management
- **Grant access**: Add users to project roles
- **Revoke access**: Remove users from project roles
- **List access**: Show all projects/roles a user has access to
- **Invite users**: Add new users to Jira who don't have accounts yet
- **Check roles**: List available roles in a project, get user's roles

### Email Communication
- **Read emails**: Fetch unread emails, search emails
- **Send emails**: Send new emails, reply in threads
- **Follow-ups**: Ask for clarification when requests are unclear
- **Notifications**: Send confirmations after actions complete

## Setup

1. **Python 3.9+**, create and activate a venv:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # macOS/Linux
   # .venv\Scripts\Activate.ps1   # Windows
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment:** Copy `.env.example` to `.env` and configure:

### Required: Google API Key
```bash
GOOGLE_API_KEY=your-gemini-api-key
```

### Required: Gmail Configuration
```bash
GMAIL_ADDRESS=your-bot@gmail.com
GMAIL_APP_PASSWORD=your-app-password
GMAIL_IMAP_HOST=imap.gmail.com  # optional, default
GMAIL_SMTP_HOST=smtp.gmail.com  # optional, default
EMAIL_BOT_NAME=Access Controller Bot  # optional
```

**How to get Gmail App Password:**
1. Enable 2-Factor Authentication on your Gmail account
2. Go to [Google Account → Security → App Passwords](https://myaccount.google.com/apppasswords)
3. Create a new app password for "Mail"
4. Use this password as `GMAIL_APP_PASSWORD`

### Required: Jira Configuration
```bash
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-jira-admin@company.com
JIRA_API_TOKEN=your-jira-api-token
```

**How to get Jira API Token:**
1. Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create API token (not "with scopes") → name it, set expiration
3. Copy the token immediately (shown only once)
4. Use the same email as `JIRA_EMAIL`

**Required Jira Permissions:** The account must have permission to manage project roles (Jira Admin or Project Admin).

## Running the Server

**Start the FastAPI server:**

```bash
uvicorn access_controller_agent.server:app --reload --port 8000
```

## API Endpoints

### POST /request
Handle any access request via natural language.

```bash
curl -X POST http://localhost:8000/request \
  -H "Content-Type: application/json" \
  -d '{"message": "Grant john@company.com Developer access to project TEST"}'
```

### POST /email/poll
Poll for new emails and process them automatically. **Use this for scheduled automation.**

```bash
curl -X POST http://localhost:8000/email/poll \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "auto_process": true}'
```

### GET /email/unread
Check unread emails without processing.

```bash
curl http://localhost:8000/email/unread?limit=10
```

### GET /health
Health check.

```bash
curl http://localhost:8000/health
```

## Example Email Requests

Users can send emails like:

- `"Please give john@company.com Developer access to PROJECT-X"`
- `"Remove Sarah's access to the TEST project"`
- `"What projects does mike@company.com have access to?"`
- `"I need admin access to PROJECT-Y for the new sprint"` (grants to sender)
- `"Add this new contractor to Jira: newuser@contractor.com"` (invites user)

## Automated Email Processing

For production, set up a cron job or scheduler to call `/email/poll` periodically:

```bash
# Every 5 minutes
*/5 * * * * curl -X POST http://localhost:8000/email/poll -H "Content-Type: application/json" -d '{"limit": 10, "auto_process": true}'
```

## ADK CLI (Development)

From the parent directory containing `access_controller_agent/`:

```bash
adk run access_controller_agent
# or
adk web --port 8000
```

## Future Integrations (Planned)

- **Bitbucket**: Repository access management
- **GitHub**: Organization and repository permissions
- **Microsoft Teams**: Team membership management
- **AWS IAM**: Cloud access permissions
