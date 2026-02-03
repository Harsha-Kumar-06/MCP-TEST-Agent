# Access Controller Agent

AI-powered organizational access authority agent built with **Google ADK**. It acts as a central, automated system for managing user access to **Atlassian products** (Jira, Confluence, Bitbucket).

## Primary Interface: Email

**Email is the main entry point** for interacting with this agent. Users send emails requesting access changes, and the agent:
1. Reads incoming emails from Gmail
2. Parses the request to understand the intent and target platform
3. Executes the appropriate action (grant/revoke access, etc.)
4. Sends a reply with the result
5. Asks follow-up questions if more information is needed

## Architecture (Hierarchical, ADK)

- **Root:** `AccessControllerCoordinator` (LlmAgent) – routes requests to specialists via LLM-driven delegation.
- **Sub-agents:**
  - **JiraAgent** – Jira project access: grant, revoke, list user access, invite new users, manage groups.
  - **ConfluenceAgent** – Confluence space permissions: grant, revoke, list access.
  - **BitbucketAgent** – Bitbucket repository permissions: grant, revoke, list access, manage workspace.
  - **EmailAgent** – Reads and processes incoming emails, sends replies, follow-ups, and notifications.

**Flow:** 
1. Email arrives → Agent fetches unread emails
2. Coordinator parses intent → Determines target platform(s)
3. Coordinator delegates to appropriate agent(s) → JiraAgent, ConfluenceAgent, or BitbucketAgent
4. Agent executes the action → Returns result
5. Coordinator → Delegates to **EmailAgent** to send reply

## Supported Platforms

| Platform | Access Type | Agent |
|----------|-------------|-------|
| **Jira** | Projects, Roles, Groups | JiraAgent |
| **Confluence** | Spaces, Permissions | ConfluenceAgent |
| **Bitbucket** | Repositories, Workspaces, Groups | BitbucketAgent |

## Capabilities

### Jira Access Management

#### User Management
- **Invite users**: Add new users to Atlassian (works for all products)
- **Look up users**: Find users by email address
- **Deactivate users**: Remove a user's entire Jira access

#### Group Management
- **List groups**: See all available groups
- **Add to group**: Add users to groups for bulk access
- **Remove from group**: Remove users from groups

#### Project Role Management
- **Grant access**: Add users to project roles (Administrator, Member, Viewer)
- **Revoke access**: Remove users from project roles
- **List access**: Show all projects/roles a user has access to

### Confluence Access Management

#### Space Permissions
- **Grant access**: Add users to spaces with read/write/admin permissions
- **Revoke access**: Remove users from spaces
- **List access**: Show all spaces a user can access
- **Check permissions**: See who has access to a specific space

#### Group Access
- **Add group to space**: Give a group access to a space
- **List groups**: See all available groups

### Bitbucket Access Management

#### Repository Permissions
- **Grant access**: Add users to repos with read/write/admin permissions
- **Revoke access**: Remove users from repositories
- **List access**: Show all repos a user can access
- **Check permissions**: See who has access to a specific repo

#### Workspace Management
- **List workspaces**: See available workspaces
- **Add member**: Add users to workspace
- **Remove member**: Remove users from workspace

#### Group Management
- **Add to group**: Add users to workspace groups
- **Remove from group**: Remove users from groups
- **Grant group repo access**: Give a group access to repositories

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

### Required: Jira & Confluence Configuration
```bash
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-atlassian-admin@company.com
JIRA_API_TOKEN=your-atlassian-api-token
```

**How to get Atlassian API Token:**
1. Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create API token (not "with scopes") → name it, set expiration
3. Copy the token immediately (shown only once)
4. This token works for **Jira and Confluence only** (not Bitbucket)

### Required: Bitbucket Configuration (Separate API Token!)
```bash
BITBUCKET_USERNAME=your-atlassian-email@company.com
BITBUCKET_API_TOKEN=your-bitbucket-api-token
BITBUCKET_WORKSPACE=your-workspace-slug  # optional, derived from JIRA_BASE_URL
```

**⚠️ IMPORTANT: Bitbucket requires a separate API token with scopes!**

The Atlassian API token (from id.atlassian.com) does NOT work with Bitbucket Cloud API.

**How to get Bitbucket API Token:**
1. Go to [Bitbucket API Tokens](https://bitbucket.org/account/settings/api-tokens/)
2. Click "Create API token"
3. Give it a name (e.g., "Access Controller Bot")
4. Select these **REQUIRED** scopes:
   - **Account**: Read
   - **Repositories**: Read, Write, Admin
   - **Projects**: Read, Admin
   - **Workspaces**: Read, Admin
   - **Permissions**: Read, **Write** ← Critical for managing user access!
5. Click "Create" and copy the token immediately (shown only once)

**Required Permissions:** The account must have admin permissions for:
- Jira: Manage project roles (Jira Admin or Project Admin)
- Confluence: Manage space permissions (Space Admin)
- Bitbucket: Manage repository permissions (Repository Admin)

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

### Jira Access
- `"Please give john@company.com Developer access to PROJECT-X"`
- `"Remove Sarah's access to the TEST project"`
- `"What projects does mike@company.com have access to?"`
- `"I need admin access to PROJECT-Y for the new sprint"` (grants to sender)
- `"Add john@company.com to the developers group"`
- `"Remove sarah from the jira-software-users group"`

### Confluence Access
- `"Give john@company.com read access to the Engineering space"`
- `"Grant admin permissions to sarah@company.com for the HR Documentation space"`
- `"Remove mike's access from the Product Specs confluence space"`
- `"What Confluence spaces does john@company.com have access to?"`
- `"Who has access to the TEAM space in Confluence?"`

### Bitbucket Access
- `"Give john@company.com write access to the backend-api repository"`
- `"Grant sarah admin access to the frontend repo in Bitbucket"`
- `"Remove mike's access from all Bitbucket repositories"`
- `"What Bitbucket repos does john@company.com have access to?"`
- `"Add the developers group to the main-service repository"`

### User Management
- `"Add this new contractor to our systems: newuser@contractor.com"` (invites user)
- `"Invite bob@external.com and give them access to KAN project and Engineering confluence space"`
- `"Deactivate jane@company.com from all systems"` (removes all access)

### Information Queries
- `"What roles are available in the TEST project?"`
- `"List all projects in Jira"`
- `"Show me all Confluence spaces"`
- `"List all Bitbucket repositories"`

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

## Atlassian Product Concepts

### Jira
| Concept | Description | Example |
|---------|-------------|---------|
| **Project** | Container for issues with a KEY | KEY: "KAN", NAME: "Kanban Board" |
| **Project Role** | Access level within a project | Administrator, Member, Viewer |
| **Group** | Collection of users for bulk access | "jira-software-users", "developers" |

### Confluence
| Concept | Description | Example |
|---------|-------------|---------|
| **Space** | Container for pages/documents | KEY: "ENG", NAME: "Engineering Docs" |
| **Permission** | Access level in a space | read, write, admin |
| **Group** | Collection of users (shared with Jira) | "confluence-users" |

### Bitbucket
| Concept | Description | Example |
|---------|-------------|---------|
| **Workspace** | Organization-level container | Derived from Atlassian domain |
| **Repository** | Code repository | "backend-api", "frontend-app" |
| **Permission** | Access level for a repo | read, write, admin |
| **Group** | Workspace-level user group | "developers", "qa-team" |

## Future Integrations (Planned)

- **GitHub**: Organization and repository permissions
- **Microsoft Teams**: Team membership management
- **AWS IAM**: Cloud access permissions
- **Google Workspace**: Shared drive and group management
