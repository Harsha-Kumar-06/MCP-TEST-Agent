# Access Controller Agent

AI-powered organizational access authority agent built with **Google ADK**. It acts as a central, automated system for managing user access (starting with **Jira**; email-based workflows and more systems can be added later).

## Architecture (Hierarchical, ADK)

- **Root:** `AccessControllerCoordinator` (LlmAgent) – routes requests to specialists via LLM-driven delegation.
- **Sub-agents:**
  - **JiraAgent** – Jira project access: grant, revoke, list user access, look up user by email. Uses Jira Cloud REST API v3.
  - **EmailAgent** – Sends emails (confirmations, approval requests, notifications). Incoming email is passed as the user message.

Flow: User (or email ingestion) sends a message → Coordinator classifies intent → Delegates to **JiraAgent** or **EmailAgent** → Sub-agent uses tools and returns result.

## Capabilities (current)

- **Jira:** Grant/revoke project role access, list user access, resolve user by email.
- **Email:** Send email (mock if SMTP not configured).
- **Coordinator:** Single entry point; delegates to Jira or Email based on natural language.

## Setup

1. **Python 3.10+**, create and activate a venv:

   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1   # Windows
   # source .venv/bin/activate   # macOS/Linux
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment:** Copy `.env.example` to `.env` and set:

   - `GOOGLE_API_KEY` – required (Gemini).
   - Optional: `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` for real Jira operations.
   - Optional: `SMTP_*` and `EMAIL_FROM` for real email sending.

**Where to get the Jira API token:** Create it at [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens). Log in with your Jira/Atlassian email → **Create API token** (not “Create API token with scopes”) → name it, set expiration → copy the token once (it’s only shown once). Use that same email as `JIRA_EMAIL` and the token as `JIRA_API_TOKEN`. Your `JIRA_BASE_URL` is your Jira Cloud URL (e.g. `https://your-company.atlassian.net`). **Scope:** use the simple token with no scopes; it inherits your account’s Jira permissions. Ensure that account can manage project roles (e.g. Jira Admin or Project Admin on the relevant projects).

## Run

**API server (FastAPI):**

```bash
uvicorn access_controller_agent.server:app --reload --port 8000
```

Then:

- **POST /request** or **POST /access** – body: `{"message": "Grant john@company.com access to project PROJ on Jira"}`.
- **GET /health** – health check.

**ADK CLI (optional):**

From the parent directory that contains `access_controller_agent/`:

```bash
adk run access_controller_agent
# or
adk web --port 8000
```

## Example requests

- `Grant john@company.com access to project PROJ on Jira`
- `Revoke jane@company.com from project PROJ`
- `What Jira access does john@company.com have?`
- `Send an email to manager@company.com saying access was granted`

Without Jira/email config, the agent still runs and reports that those systems are not configured.
