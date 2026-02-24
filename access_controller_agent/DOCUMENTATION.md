# Access Controller Agent

An autonomous AI-powered organizational access management system built with Google ADK. It acts as a central authority for managing user access across multiple platforms (Jira, Confluence, Bitbucket, GitHub) via email-driven workflows.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture & Design Pattern](#architecture--design-pattern)
- [System Flowcharts](#system-flowcharts)
- [Component Deep Dive](#component-deep-dive)
- [Service Layer](#service-layer)
- [Tools Layer](#tools-layer)
- [Agent Specifications](#agent-specifications)
- [Implementation Details](#implementation-details)
- [API & Class Reference](#api--class-reference)
- [Email Integration](#email-integration)
- [Platform Integration](#platform-integration)
- [How to Run](#how-to-run)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)

---

## Project Overview

Managing user access across multiple enterprise platforms is complex, time-consuming, and error-prone. IT teams spend hours manually processing access requests, looking up users across systems, and ensuring proper permissions. This creates bottlenecks in onboarding, project kickoffs, and access revocations.

This system **fully automates the access management workflow** through a conversational email interface powered by AI:

1. **Users send natural language emails** requesting access changes
2. **AI agent parses intent** and extracts target platform, user, resource, and permission level
3. **Agent autonomously executes actions** across Jira, Confluence, Bitbucket, and GitHub
4. **Agent sends threaded email replies** confirming actions or asking follow-up questions
5. **Background polling service** continuously monitors the inbox for new requests

### Key Features

- **Email-first interface** — Users interact via email (no special forms or portals)
- **Thread-aware replies** — All responses maintain email conversation threads
- **Autonomous execution** — Agent uses intelligent defaults (no permission asking)
- **Multi-platform support** — Single interface for Jira, Confluence, Bitbucket, GitHub
- **Auto-invitations** — Automatically invites users who don't exist in the organization
- **Smart filtering** — Ignores newsletters/marketing; only processes access requests
- **Background polling** — Checks inbox every 30 seconds (configurable)
- **Hierarchical agents** — Coordinator delegates to platform-specific specialists

### Supported Platforms

| Platform | Access Types | Key Operations |
|----------|-------------|----------------|
| **Jira** | Projects (roles), Groups, User invitations | Grant, Revoke, List access, Add to groups |
| **Confluence** | Spaces (permissions), Groups | Grant, Revoke, List access, Add groups to spaces |
| **Bitbucket** | Repositories, Workspaces, Groups | Grant, Revoke, List access, Manage workspace members |
| **GitHub** | Organizations, Repositories, Teams | Invite, Grant repo access, Add to teams, Team-repo access |

---

## Architecture & Design Pattern

**Pattern**: Event-Driven Hierarchical Multi-Agent with Email Orchestration

The system is structured around four layers:

### 1. Email Polling Layer

**FastAPI Lifespan Background Task** ([server.py](server.py))
- Runs `email_polling_task()` continuously in the background
- Polls Gmail every 30 seconds (configurable via `EMAIL_POLL_INTERVAL`)
- Filters emails using `is_access_request()` (checks for keywords like "access", "grant", "jira")
- Ignores marketing/newsletter emails (noreply@, marketing@, etc.)
- Queues legitimate access requests for agent processing

### 2. Service Layer

**Platform API Clients** (in root directory: `jira_service.py`, `email_service.py`, etc.)
- **JiraService**: Jira Cloud REST API v3 client (projects, roles, groups, users)
- **ConfluenceService**: Confluence Cloud REST API v2 client (spaces, permissions)
- **BitbucketService**: Bitbucket Cloud API 2.0 client (repositories, workspaces, groups)
- **GitHubService**: GitHub REST API client using GitHub App authentication (org, repos, teams)
- **EmailService**: Gmail IMAP (read) + SMTP (send) client with app password auth
- **AtlassianAdminService**: Atlassian Admin API for org-level user invitations and approvals

Each service handles:
- Authentication (API tokens, app passwords, JWT for GitHub App)
- HTTP requests with error handling
- Data transformation (API responses → standardized dicts)
- Rate limiting and retries

### 3. Tools Layer

**Function Tools** ([tools.py](tools.py))
- 70+ Python functions exposed to agents as tools
- Organized by platform:
  - **Organization tools**: `invite_user_to_org`, `check_user_in_org`, `approve_pending_user_request`
  - **Jira tools** (25 functions): `jira_grant_access`, `jira_revoke_access`, `jira_add_user_to_group`, etc.
  - **Confluence tools** (9 functions): `confluence_grant_space_access`, `confluence_list_user_access`, etc.
  - **Bitbucket tools** (13 functions): `bitbucket_grant_repository_access`, `bitbucket_add_workspace_member`, etc.
  - **GitHub tools** (13 functions): `github_invite_user_to_org`, `github_grant_repository_access`, etc.
  - **Email tools** (7 functions): `email_reply`, `send_email`, `email_fetch_unread`, etc.
- Each tool returns `dict[str, Any]` with `status: "success" | "error"` and relevant data
- Tools automatically invoke services and handle edge cases (e.g., auto-invite if user doesn't exist)

### 4. Agent Layer (Google ADK)

**Hierarchical agent structure**:

```
root_agent (LlmAgent - Coordinator)
 ├── jira_agent (LlmAgent)
 │    └── tools: jira_*, invite_user_to_org, check_user_in_org
 ├── confluence_agent (LlmAgent)
 │    └── tools: confluence_*, invite_user_to_org
 ├── bitbucket_agent (LlmAgent)
 │    └── tools: bitbucket_*, invite_user_to_org
 ├── github_agent (LlmAgent)
 │    └── tools: github_*
 └── email_agent (LlmAgent)
      └── tools: email_reply, send_email
```

**Execution Flow**:
1. **Email arrives** → Background polling task fetches it
2. **Coordinator parses email** → Extracts: sender, action, platform, user, resource, permission
3. **Coordinator delegates** → Transfers to appropriate sub-agent(s) (JiraAgent, ConfluenceAgent, etc.)
4. **Sub-agent executes** → Calls tools (e.g., `jira_grant_access(user, project, role)`)
5. **Coordinator collects result** → Gathers success/failure from sub-agent
6. **Coordinator delegates to EmailAgent** → Sends threaded reply with Email ID for conversation threading
7. **EmailAgent sends reply** → Uses `email_reply(original_email_id, body)` to maintain thread

---

## System Flowcharts

### 1. System Architecture Overview

![System Architecture](docs/system_architecture.svg)

Complete system overview showing the data flow from Gmail inbox through the FastAPI polling layer, Google ADK agent pipeline, tools layer, service layer, and external platform APIs.

### 2. End-to-End Email Processing Flow

![Email Processing Flow](docs/email_processing_flow.svg)

Complete process flowchart from email arrival through polling, filtering, agent processing, and final reply. Shows the decision point for access request filtering and the full execution pipeline.

### 3. Hierarchical Agent Delegation Detail

![Hierarchical Delegation](docs/hierarchical_delegation.svg)

Detailed view of the hierarchical multi-agent pattern showing how the Coordinator parses intent, delegates to specialized sub-agents (ConfluenceAgent, JiraAgent) in parallel, synthesizes results, and sends email replies via EmailAgent.

---

## Service Layer

Services are platform-specific API clients located in the root `access_controller_agent/` directory.

### jira_service.py

**Class: `JiraService`**

Jira Cloud REST API v3 client for project role and user operations.

#### Configuration

```python
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=admin@company.com
JIRA_API_TOKEN=your_atlassian_api_token
```

#### Key Methods

**`get_user_by_email(email) → dict`**
- Searches users by email via `/user/search?query={email}`
- Returns: `{status, account_id, display_name, email}`
- Handles hidden emails (Jira privacy settings) by returning first search result

**`invite_user(email) → dict`**
- Invites new user to Jira via `/user` endpoint
- Auto-invites if user doesn't exist in org
- Returns: `{status, message, account_id}`

**`list_projects() → list[dict]`**
- Fetches all accessible projects via `/project/search`
- Returns: `[{key, name, project_type_key, lead_account_id}]`

**`get_project(project_key) → dict`**
- Fetches single project details
- Returns: `{key, name, description, lead, project_type}`

**`get_project_roles(project_key) → dict`**
- Fetches all roles for a project (Administrator, Member, Viewer, etc.)
- Returns: `{role_name: role_id, ...}`

**`get_role_actors(project_key, role_id) → list[dict]`**
- Fetches users/groups assigned to a role
- Returns: `[{type: "atlassian-user-role-actor", account_id, display_name}]`

**`assign_project_role(project_key, role_id, account_id) → dict`**
- Assigns user to project role
- HTTP POST to `/project/{key}/role/{roleId}`
- Returns: `{status, message}`

**`remove_project_role(project_key, role_id, account_id) → dict`**
- Removes user from project role
- HTTP DELETE to `/project/{key}/role/{roleId}?user={accountId}`

**`list_groups(max_results) → list[dict]`**
- Lists all groups
- Returns: `[{name, group_id}]`

**`get_group_members(group_name, max_results) → dict`**
- Lists users in a group
- Returns: `{values: [{account_id, display_name, email}]}`

**`add_user_to_group(group_name, account_id) → dict`**
- Adds user to group
- HTTP POST to `/group/user`

**`remove_user_from_group(group_name, account_id) → dict`**
- Removes user from group
- HTTP DELETE to `/group/user?groupname={}&accountId={}`

**`deactivate_user(account_id) → dict`**
- Removes all user's Jira access
- HTTP DELETE to `/user?accountId={}`

### email_service.py

**Class: `EmailService`**

Gmail IMAP (reading) and SMTP (sending) client using app password authentication.

#### Configuration

```python
GMAIL_ADDRESS=bot@company.com
GMAIL_APP_PASSWORD=your_app_password
GMAIL_IMAP_HOST=imap.gmail.com  # default
GMAIL_SMTP_HOST=smtp.gmail.com  # default
EMAIL_BOT_NAME=Access Controller Bot  # default
```

#### Key Methods

**`fetch_unread_emails(limit, days_back) → dict`**
- Connects to IMAP
- Searches for UNSEEN emails in last `days_back` days
- Parses each email: `{id, from, from_email, subject, date, body, message_id, in_reply_to, references}`
- Returns: `{status: "success", emails: [...]}`

**`get_email_by_id(email_id) → dict`**
- Fetches specific email by numeric ID
- Returns email dict with all fields

**`mark_as_read(email_id) → dict`**
- Marks email as SEEN
- IMAP STORE command

**`search_emails(query, limit) → dict`**
- Searches emails by IMAP query string
- Example: `SUBJECT "access request"`, `FROM "user@company.com"`

**`send_email(to, subject, body) → dict`**
- Sends new email via SMTP
- Uses `formataddr()` to set "From" display name
- Returns: `{status: "success", message: "Email sent"}`

**`reply_to_email(original_email_id, reply_body, include_original) → dict`**
- **Critical for email threading**
- Fetches original email headers: `Message-ID`, `References`
- Constructs reply with proper headers:
  - `In-Reply-To`: Original `Message-ID`
  - `References`: Original `References` + original `Message-ID`
  - `Subject`: `Re: {original_subject}`
- Sends via SMTP
- Ensures reply appears in same thread in Gmail/Outlook

### confluence_service.py

**Class: `ConfluenceService`**

Confluence Cloud REST API v2 client for space permissions.

#### Configuration

```python
# Uses same credentials as Jira
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=admin@company.com
JIRA_API_TOKEN=your_atlassian_api_token
```

#### Key Methods

**`list_spaces(limit) → list[dict]`**
- Fetches all spaces via `/wiki/api/v2/spaces`
- Returns: `[{id, key, name, description}]`

**`get_space(space_key) → dict`**
- Fetches single space details
- Returns: `{id, key, name, status, description}`

**`get_space_permissions(space_id) → dict`**
- Fetches all permissions for a space
- Returns: `{status, permissions: [{principal, operation, targetType}]}`

**`add_space_permission(space_id, principal_id, principal_type, operation) → dict`**
- Grants space permission (read, write, admin)
- `principal_type`: "user" or "group"
- `operation`: "read", "write", "administer"
- HTTP POST to `/wiki/api/v2/spaces/{spaceId}/permissions`

**`remove_space_permission(space_id, permission_id) → dict`**
- Revokes space permission
- HTTP DELETE to `/wiki/api/v2/spaces/{spaceId}/permissions/{permissionId}`

**`invite_user(email) → dict`**
- Invites user to Confluence
- Uses Confluence-specific invite endpoint

### bitbucket_service.py

**Class: `BitbucketService`**

Bitbucket Cloud API 2.0 client for repository and workspace management.

#### Configuration

```python
BITBUCKET_USERNAME=your_atlassian_email@company.com
BITBUCKET_API_TOKEN=your_bitbucket_api_token  # ⚠️ Separate from Atlassian token!
BITBUCKET_WORKSPACE=your-workspace-slug  # optional, auto-derived
```

**⚠️ CRITICAL**: Bitbucket requires a separate API token with scopes:
- Account: Read
- Repositories: Read, Write, Admin
- Workspaces: Read, Admin
- **Permissions: Write** ← Required for managing user access!

#### Key Methods

**`list_workspaces() → list[dict]`**
- Lists accessible workspaces
- Returns: `[{slug, name, uuid}]`

**`get_workspace_members(workspace) → list[dict]`**
- Lists workspace members
- Returns: `[{display_name, account_id, uuid}]`

**`add_workspace_member(workspace, account_id) → dict`**
- Adds user to workspace as member
- HTTP PUT to `/workspaces/{workspace}/members/{account_id}`

**`remove_workspace_member(workspace, account_id) → dict`**
- Removes workspace member
- HTTP DELETE

**`list_repositories(workspace, limit) → list[dict]`**
- Lists repositories in workspace
- Returns: `[{slug, name, is_private, mainbranch}]`

**`get_repository(workspace, repo_slug) → dict`**
- Fetches single repository details

**`add_repository_permission(workspace, repo_slug, account_id, permission) → dict`**
- Grants repository access (read, write, admin)
- HTTP PUT to `/repositories/{workspace}/{repo_slug}/permissions-config/users/{account_id}`

**`remove_repository_permission(workspace, repo_slug, account_id) → dict`**
- Revokes repository access

**`list_groups(workspace) → list[dict]`**
- Lists workspace groups
- Returns: `[{slug, name}]`

**`add_user_to_group(workspace, group_slug, account_id) → dict`**
- Adds user to workspace group

### github_service.py

**Class: `GitHubService`**

GitHub REST API client using GitHub App authentication (JWT + installation token).

#### Configuration

```python
GITHUB_ORG=your-github-org
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...
GITHUB_INSTALLATION_ID=987654  # optional, auto-resolved
GITHUB_API_BASE_URL=https://api.github.com  # default
GITHUB_API_VERSION=2022-11-28  # default
```

**Authentication Flow**:
1. Generate JWT using `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY`
2. Use JWT to fetch installation token via `/app/installations/{id}/access_tokens`
3. Use installation token for all API requests (expires in 1 hour, auto-refreshed)

#### Key Methods

**`invite_user_to_org(username_or_email, role) → dict`**
- Invites user to GitHub organization
- Tries to resolve email → GitHub username via `/search/users?q={email}`
- Creates invitation via `/orgs/{org}/invitations`
- `role`: "member" or "admin"

**`remove_member(username) → dict`**
- Removes organization member
- HTTP DELETE to `/orgs/{org}/members/{username}`

**`list_members(filter) → list[dict]`**
- Lists organization members
- `filter`: "all", "2fa_disabled"
- Returns: `[{login, id, type, site_admin}]`

**`list_pending_invitations() → list[dict]`**
- Lists pending org invitations
- Returns: `[{email, login, role, created_at}]`

**`list_repositories(limit) → list[dict]`**
- Lists organization repositories
- Returns: `[{name, full_name, private, default_branch}]`

**`add_collaborator(repo, username, permission) → dict`**
- Grants repository access
- `permission`: pull, push, admin, maintain, triage
- HTTP PUT to `/repos/{org}/{repo}/collaborators/{username}`

**`remove_collaborator(repo, username) → dict`**
- Removes repository collaborator

**`get_user_permission(repo, username) → dict`**
- Gets effective user permission for repository
- Returns: `{permission: "pull" | "push" | "admin"}`

**`list_teams() → list[dict]`**
- Lists organization teams
- Returns: `[{slug, name, description, privacy}]`

**`add_team_member(team_slug, username, role) → dict`**
- Adds user to team
- `role`: "member" or "maintainer"

**`remove_team_member(team_slug, username) → dict`**
- Removes team member

**`add_team_repo(team_slug, repo, permission) → dict`**
- Grants team access to repository

**`remove_team_repo(team_slug, repo) → dict`**
- Revokes team access from repository

### bitbucket_service.py (AtlassianAdminService)

**Class: `AtlassianAdminService`**

Atlassian Admin API client for organization-level operations (user invitations, approvals).

#### Configuration

```python
# Uses same credentials as Jira/Confluence
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=admin@company.com
JIRA_API_TOKEN=your_atlassian_api_token
```

#### Key Methods

**`get_org_id() → str`**
- Retrieves Atlassian organization ID
- Required for Admin API calls

**`is_user_in_org(email) → dict`**
- Checks if user exists in organization
- Returns: `{status, in_org: bool, account_id, name}`

**`invite_user_to_org(email, products) → dict`**
- Invites user with immediate access to products
- `products`: ["jira", "confluence", "bitbucket"] or None for all
- Returns: `{status, message, invited_products}`

**`list_pending_requests(email) → dict`**
- Lists pending access requests for a user

**`auto_approve_user_request(email, products) → dict`**
- Automatically approves pending access request
- Called after product-specific invitations
- Grants immediate access (no admin manual approval needed)

---

## Tools Layer

The `tools.py` file contains 70+ functions organized by platform. Each tool:
- **Input**: Typed parameters (email, project_key, permission, etc.)
- **Output**: `dict[str, Any]` with `status: "success" | "error"` and relevant data
- **Error Handling**: Catches exceptions, logs errors, returns structured error dicts
- **Service Integration**: Calls appropriate service method and transforms response

### Tool Categories

#### Organization Tools (4 functions)

| Function | Purpose |
|----------|---------|
| `invite_user_to_org(email, products)` | Invite user to Atlassian org with product access |
| `check_user_in_org(email)` | Check if user exists in org |
| `list_pending_access_requests(email)` | List pending access requests |
| `approve_pending_user_request(email, products)` | Auto-approve pending requests |

#### Jira Tools (25 functions)

| Function | Purpose |
|----------|---------|
| `jira_get_user_by_email(email)` | Look up user by email |
| `jira_invite_user(email)` | Invite user to Jira |
| `jira_invite_and_grant_access(email, project, role)` | Invite + grant in one call |
| `jira_grant_access(email, project, role)` | Grant project role access |
| `jira_revoke_access(email, project, role)` | Revoke project role access |
| `jira_revoke_all_project_access(email, project)` | Remove all roles for user in project |
| `jira_get_user_access_details(email, project)` | Show direct vs group access |
| `jira_list_user_access(email)` | List all projects user has access to |
| `jira_list_project_roles(project)` | List available roles in project |
| `jira_get_user_roles_in_project(email, project)` | Get user's specific roles |
| `jira_list_groups(max_results)` | List all groups |
| `jira_get_group_members(group, max)` | List members of a group |
| `jira_add_user_to_group(email, group)` | Add user to group |
| `jira_remove_user_from_group(email, group)` | Remove user from group |
| `jira_get_user_groups(email)` | List user's group memberships |
| `jira_list_projects(max_results)` | List all projects |
| `jira_get_project(project_key)` | Get project details |
| `jira_deactivate_user(email)` | Remove all Jira access |

#### Confluence Tools (9 functions)

| Function | Purpose |
|----------|---------|
| `confluence_list_spaces(limit)` | List all spaces |
| `confluence_get_space(space_name_or_key)` | Get space details |
| `confluence_get_space_permissions(space)` | List space permissions |
| `confluence_grant_space_access(email, space, permission)` | Grant space access |
| `confluence_revoke_space_access(email, space)` | Revoke space access |
| `confluence_add_group_to_space(group, space, permission)` | Grant group access to space |
| `confluence_list_user_access(email)` | List user's space access |
| `confluence_list_groups(limit)` | List all groups |
| `confluence_get_group_members(group, limit)` | List group members |

#### Bitbucket Tools (13 functions)

| Function | Purpose |
|----------|---------|
| `bitbucket_list_workspaces()` | List accessible workspaces |
| `bitbucket_get_workspace_members(workspace)` | List workspace members |
| `bitbucket_add_workspace_member(email, workspace)` | Add member to workspace |
| `bitbucket_remove_workspace_member(email, workspace)` | Remove workspace member |
| `bitbucket_list_repositories(workspace, limit)` | List repositories |
| `bitbucket_get_repository(repo_slug, workspace)` | Get repository details |
| `bitbucket_get_repository_permissions(repo, workspace)` | List repo permissions |
| `bitbucket_grant_repository_access(email, repo, permission, workspace)` | Grant repo access |
| `bitbucket_revoke_repository_access(email, repo, workspace)` | Revoke repo access |
| `bitbucket_add_group_to_repository(group, repo, permission, workspace)` | Grant group repo access |
| `bitbucket_remove_group_from_repository(group, repo, workspace)` | Revoke group repo access |
| `bitbucket_list_user_access(email, workspace)` | List user's repo access |
| `bitbucket_list_groups(workspace)` | List workspace groups |
| `bitbucket_get_group_members(group, workspace)` | List group members |
| `bitbucket_add_user_to_group(email, group, workspace)` | Add user to group |
| `bitbucket_remove_user_from_group(email, group, workspace)` | Remove user from group |

#### GitHub Tools (13 functions)

| Function | Purpose |
|----------|---------|
| `github_invite_user_to_org(user_identifier, role)` | Invite user to GitHub org |
| `github_remove_user_from_org(username)` | Remove org member |
| `github_list_org_members(filter)` | List organization members |
| `github_list_org_invitations()` | List pending invitations |
| `github_list_org_repositories(limit)` | List org repositories |
| `github_grant_repository_access(user, repo, permission)` | Grant repo collaborator access |
| `github_revoke_repository_access(user, repo)` | Remove repository collaborator |
| `github_get_repository_user_permission(user, repo)` | Check user's repo permission |
| `github_list_repository_collaborators(repo, affiliation)` | List repo collaborators |
| `github_list_teams()` | List organization teams |
| `github_add_user_to_team(user, team_slug, role)` | Add user to team |
| `github_remove_user_from_team(username, team_slug)` | Remove team member |
| `github_grant_team_repo_access(team_slug, repo, permission)` | Grant team access to repo |
| `github_revoke_team_repo_access(team_slug, repo)` | Revoke team repo access |

#### Email Tools (7 functions)

| Function | Purpose |
|----------|---------|
| `email_fetch_unread(limit)` | Fetch unread emails |
| `email_get_by_id(email_id)` | Get specific email |
| `email_mark_as_read(email_id)` | Mark email as read |
| `email_search(query, limit)` | Search emails by query |
| `send_email(to, subject, body)` | Send new email |
| `email_reply(original_email_id, reply_body, include_original)` | **Reply to email (maintains thread)** |
| `email_send_followup(original_email_id, question, context)` | Send follow-up question |

---

## Agent Specifications

### Root Agent: AccessControllerCoordinator

| Attribute | Value |
|-----------|-------|
| **ADK Class** | `LlmAgent` |
| **Name** | `AccessControllerCoordinator` |
| **Model** | `gemini-2.0-flash` |
| **Sub-agents** | JiraAgent, ConfluenceAgent, BitbucketAgent, GitHubAgent, EmailAgent |
| **Tools** | None directly (delegates to sub-agents) |
| **Role** | Parses incoming emails, routes to specialists, sends replies |

**Key Behaviors**:
- **Autonomous execution**: Never asks "should I proceed?" — uses intelligent defaults
- **Multi-platform routing**: Detects platform mentions (jira, confluence, github) and delegates appropriately
- **Email threading**: Always passes `Email ID` to `EmailAgent` for proper conversation threading
- **Intelligent defaults**:
  - Jira role: "Member" (unless "admin" or "viewer" specified)
  - Confluence permission: "write" (unless "read" or "admin" specified)
  - Bitbucket permission: "write" for developers
  - GitHub permission: "push" for developers
- **Comprehensive queries**: "Does X have access?" → checks ALL platforms automatically

### Sub-Agent: JiraAgent

| Attribute | Value |
|-----------|-------|
| **ADK Class** | `LlmAgent` |
| **Name** | `JiraAgent` |
| **Model** | `gemini-2.0-flash` |
| **Tools** | All `jira_*` functions + `invite_user_to_org` + `check_user_in_org` |
| **Focus** | Jira project access, roles, groups, user management |

**Key Behaviors**:
- **Auto-invite**: If user not found, automatically calls `invite_user_to_org()` then grants access
- **Direct vs Group access detection**: Before revoking, checks `jira_get_user_access_details()` to understand access type
- **Project name resolution**: Auto-resolves project names to keys using `jira_list_projects()`
- **Smart group selection**: Knows about Atlassian standard groups (`jira-software-users`, `jira-admins-{site}`)

**Example Instructions Excerpt**:
```
Default role: "Member" (unless user specifies "admin" or "viewer")
Auto-invite: If user doesn't exist, tools invite AND auto-approve access
Don't ask "should I invite?" — tools handle automatically
```

### Sub-Agent: ConfluenceAgent

| Attribute | Value |
|-----------|-------|
| **ADK Class** | `LlmAgent` |
| **Name** | `ConfluenceAgent` |
| **Model** | `gemini-2.0-flash` |
| **Tools** | All `confluence_*` functions + `invite_user_to_org` |
| **Focus** | Confluence space permissions, group access |

**Key Behaviors**:
- **Permission mapping**: "editor" → write, "viewer" → read, "admin" → administer
- **Space key resolution**: Auto-resolves space names to keys
- **Group permissions**: Can grant groups access to spaces (bulk access)

### Sub-Agent: BitbucketAgent

| Attribute | Value |
|-----------|-------|
| **ADK Class** | `LlmAgent` |
| **Name** | `BitbucketAgent` |
| **Model** | `gemini-2.0-flash` |
| **Tools** | All `bitbucket_*` functions + `invite_user_to_org` |
| **Focus** | Bitbucket repository access, workspace membership, groups |

**Key Behaviors**:
- **Workspace auto-resolution**: Uses `BITBUCKET_WORKSPACE` env var or auto-detects from domain
- **Permission levels**: read, write, admin
- **Workspace vs Repository access**: Understands difference between workspace member and repo collaborator

### Sub-Agent: GitHubAgent

| Attribute | Value |
|-----------|-------|
| **ADK Class** | `LlmAgent` |
| **Name** | `GitHubAgent` |
| **Model** | `gemini-2.0-flash` |
| **Tools** | All `github_*` functions |
| **Focus** | GitHub organization membership, repository collaborators, teams |

**Key Behaviors**:
- **Email → username resolution**: Attempts to resolve email to GitHub username via search API
- **Permission mapping**: pull, push, admin, maintain, triage
- **Team-based access**: Can grant teams access to repositories
- **GitHub App authentication**: Uses JWT + installation token flow

### Sub-Agent: EmailAgent

| Attribute | Value |
|-----------|-------|
| **ADK Class** | `LlmAgent` |
| **Name** | `EmailAgent` |
| **Model** | `gemini-2.0-flash` |
| **Tools** | `email_reply`, `send_email` |
| **Focus** | Sending email replies, confirmations, follow-ups |

**Key Behaviors**:
- **CRITICAL**: Always uses `email_reply(original_email_id, body)` when Email ID provided
- **Proper threading**: Maintains email conversation threads (In-Reply-To, References headers)
- **Three message types**:
  1. **Success confirmation**: "✓ Granted X access to Y"
  2. **Follow-up question**: "Which project did you mean? Found: A, B, C"
  3. **Error notification**: "Unable to process: [reason]"
- **Professional tone**: Friendly, concise, no technical jargon

**Example Instructions Excerpt**:
```
CRITICAL: Always use email_reply when original_email_id is provided!
This maintains the email thread so users see all messages in one conversation.

Structure:
- If original_email_id provided: Use email_reply(original_email_id, reply_body)
- Otherwise: Use send_email(to, subject, body) with subject "Re: [original subject]"
```

---

## Implementation Details

### Email Threading Architecture

**Why Threading Matters**:
- Users expect email conversations to stay in one thread
- Without proper headers, replies appear as separate emails
- Threading shows full context of request → action → response

**How It Works**:
1. **Incoming email** contains headers:
   - `Message-ID`: Unique identifier (e.g., `<abc123@mail.gmail.com>`)
   - `References`: Chain of prior messages in thread
2. **`EmailService.fetch_unread_emails()`** extracts these headers and stores in email dict as `message_id`, `references`, `in_reply_to`
3. **`server.py`** passes `Email ID` and `Message-ID` to agent in prompt
4. **Coordinator** includes Email ID when delegating to `EmailAgent`
5. **`EmailAgent`** calls `email_reply(original_email_id, body)`
6. **`EmailService.reply_to_email()`**:
   - Fetches original email headers
   - Constructs reply with:
     - `In-Reply-To: <original Message-ID>`
     - `References: <original References> <original Message-ID>`
     - `Subject: Re: <original subject>`
   - Sends via SMTP

**Email Header Example**:
```
Original Email:
Message-ID: <abc123@mail.gmail.com>
References: <xyz789@mail.gmail.com>

Reply:
In-Reply-To: <abc123@mail.gmail.com>
References: <xyz789@mail.gmail.com> <abc123@mail.gmail.com>
Subject: Re: Access request for John
```

### Intelligent Defaults System

The agent avoids asking permission by using context-aware defaults:

| Context | Default Applied |
|---------|----------------|
| **Jira role** (unspecified) | "Member" |
| **User says "admin"** | "Administrator" |
| **User says "viewer" / "read-only"** | "Viewer" |
| **Confluence permission** (unspecified) | "write" |
| **User says "editor"** | "write" |
| **User says "admin"** | "administer" |
| **Bitbucket permission** ("developer") | "write" |
| **Bitbucket permission** ("admin") | "admin" |
| **GitHub repo permission** ("developer") | "push" |
| **GitHub team role** (unspecified) | "member" |
| **Workspace** (Bitbucket, unspecified) | From `BITBUCKET_WORKSPACE` or auto-derived |

### Auto-Invitation Flow

When a tool encounters a user who doesn't exist:

1. **Tool detects user not found** (e.g., `jira_get_user_by_email()` returns error)
2. **Tool calls internal helper**: `_auto_invite_user_if_needed(email, ["jira"])`
3. **Helper tries Admin API**: `AtlassianAdminService.invite_user_to_org(email, ["jira"])`
   - If Admin API succeeds → User has immediate access
4. **If Admin API unavailable**: Falls back to product-specific invite:
   - `JiraService.invite_user(email)` — creates invitation
   - `AtlassianAdminService.auto_approve_user_request(email, ["jira"])` — auto-approves
5. **Tool proceeds** with original operation (e.g., `jira_grant_access()`)

**No user interaction required** — the agent handles the entire flow autonomously.

### Background Polling vs Manual Triggering

**Background Polling** (Production Mode):
- Enabled by default (`EMAIL_POLL_ENABLED=true`)
- Runs continuously in `asyncio.create_task(email_polling_task())`
- Checks inbox every 30 seconds
- Zero user intervention — fully autonomous

**Manual Triggering** (Development/Testing):
- `POST /email/poll` endpoint
- On-demand email fetch and processing
- Useful for testing specific scenarios
- Can disable background polling: `EMAIL_POLL_ENABLED=false`

### Session Isolation

Each email request gets a unique ADK session:
```python
session_id = str(uuid.uuid4())  # e.g., "d3f4a5b6-..."
await session_service.create_session(
    app_name="access_controller",
    user_id="api_user",
    session_id=session_id
)
```

**Benefits**:
- Prevents context leakage between requests
- Enables concurrent email processing
- Allows request tracing (session ID in logs)

### Error Handling Strategy

**At Service Layer**:
- HTTP errors → Return `{status: "error", error: "message"}`
- Timeouts → Retry once, then return error
- Authentication failures → Log warning, return error

**At Tools Layer**:
- Catch all exceptions
- Log full traceback
- Return `{status: "error", error: str(e)}`

**At Server Layer**:
- `process_single_email()` wraps agent call in try/except
- On error:
  - Attempt to send error notification email (with threading)
  - Mark email as read (prevent reprocessing)
  - Log error with email ID for debugging

**At Agent Layer**:
- Coordinator interprets tool errors
- Delegates to `EmailAgent` to notify user
- Professional error messages (no stack traces to users)

---

## API & Class Reference

### server.py

#### `lifespan(app: FastAPI) → AsyncContextManager`
Manages startup/shutdown for FastAPI app.

#### `email_polling_task() → None`
Background async loop that polls Gmail every `EMAIL_POLL_INTERVAL` seconds.

#### `is_access_request(email_data: dict) → bool`
Filters emails by keywords and sender patterns.

**Parameters**:
- `email_data`: Email dict with `from_email`, `subject`, `body`

**Returns**: `True` if email looks like access request, `False` otherwise.

#### `async process_single_email(email_data: dict) → dict`
Processes one email through the agent pipeline.

**Returns**: `{email_id, from, subject, status: "processed" | "error", response | error}`

#### `async run_agent(message: str, session_id: Optional[str] = None) → str`
Runs root_agent with a message.

**Returns**: Final agent response as string.

#### `POST /request`
**Request**: `{"message": str}`  
**Response**: `{"response": str}`

#### `POST /email/poll`
**Request**: `{"limit": int, "auto_process": bool}`  
**Response**: `{"emails_found": int, "processed": int, "results": [...]}`

#### `GET /email/unread?limit=10`
**Response**: `{"status": "success", "emails": [...]}`

#### `GET /email/status`
**Response**: `{"polling_enabled": bool, "poll_interval_seconds": int}`

### Services

See [Service Layer](#service-layer) section for detailed method signatures.

### Tools

See [Tools Layer](#tools-layer) section for complete function list.

---

## Email Integration

### Gmail App Password Setup

1. **Enable 2-Factor Authentication** on Gmail account
2. Navigate to [Google Account → Security → App Passwords](https://myaccount.google.com/apppasswords)
3. Click "Generate new app password"
4. Select "Mail" as the app
5. Copy the 16-character password
6. Set in `.env`: `GMAIL_APP_PASSWORD=your_16_char_password`

### Email Filtering Logic

**Access Request Keywords** (case-insensitive):
```python
access, grant, revoke, remove, add, permission,
jira, project, role, developer, admin, administrator,
onboard, offboard, invite, user, member, team
```

**Ignored Senders**:
```python
noreply@, no-reply@, newsletter@, marketing@, info@,
notifications@, updates@, news@, promo@, support@
```

**Algorithm**:
1. Check sender against `IGNORE_SENDERS` → Skip if match
2. Search `subject` + `body` for any `ACCESS_REQUEST_KEYWORDS` → Process if found
3. Otherwise → Skip

### Email Threading Best Practices

**DO**:
- ✅ Always use `email_reply(original_email_id, body)` when Email ID available
- ✅ Include Email ID in agent prompts
- ✅ Pass Email ID when delegating to EmailAgent

**DON'T**:
- ❌ Use `send_email()` when you have Email ID (breaks threading)
- ❌ Manually construct `In-Reply-To` headers (let EmailService handle it)
- ❌ Forget to extract `message_id` from incoming emails

---

## Platform Integration

### Jira & Confluence

**API Token Generation**:
1. Go to [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token" (NOT "with scopes")
3. Name it (e.g., "Access Controller Bot")
4. Copy token immediately (shown only once)
5. Set in `.env`:
   ```env
   JIRA_BASE_URL=https://your-company.atlassian.net
   JIRA_EMAIL=admin@company.com
   JIRA_API_TOKEN=your_token_here
   ```

**Required Permissions**:
- **Jira**: Manage project roles (Jira Admin or Project Admin)
- **Confluence**: Manage space permissions (Space Admin)

### Bitbucket

**⚠️ CRITICAL**: Bitbucket requires a **separate API token** with scopes!

**API Token Generation**:
1. Go to [Bitbucket API Tokens](https://bitbucket.org/account/settings/api-tokens/)
2. Click "Create API token"
3. Name it (e.g., "Access Controller Bot")
4. Select scopes:
   - ✅ Account: Read
   - ✅ Repositories: Read, Write, Admin
   - ✅ Projects: Read, Admin
   - ✅ Workspaces: Read, Admin
   - ✅ **Permissions: Write** ← Required for managing access!
5. Click "Create" and copy token
6. Set in `.env`:
   ```env
   BITBUCKET_USERNAME=your_atlassian_email@company.com
   BITBUCKET_API_TOKEN=your_bitbucket_token
   BITBUCKET_WORKSPACE=your-workspace-slug
   ```

**Required Permissions**:
- Repository Admin for repositories being managed

### GitHub

**GitHub App Setup**:
1. **Create GitHub App**:
   - Go to GitHub → Settings → Developer settings → GitHub Apps → New GitHub App
   - Name: "Access Controller Bot"
   - Homepage URL: Your server URL
   - Webhook: Disable (not needed)
   - Permissions:
     - ✅ Organization members: Read and write
     - ✅ Repository administration: Read and write
     - ✅ Metadata: Read-only
2. **Generate Private Key**:
   - Scroll to "Private keys" section
   - Click "Generate a private key"
   - Download `.pem` file
3. **Install GitHub App**:
   - Go to "Install App" tab
   - Install on your organization
   - Copy `Installation ID` from URL (e.g., `/installations/12345678`)
4. **Configure Environment**:
   ```env
   GITHUB_ORG=your-github-org
   GITHUB_APP_ID=123456
   GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\nMII...\n-----END RSA PRIVATE KEY-----
   GITHUB_INSTALLATION_ID=12345678
   ```

**Note**: For `GITHUB_APP_PRIVATE_KEY`, replace actual newlines with `\n`:
```bash
# Convert PEM file
cat private-key.pem | tr '\n' '|' | sed 's/|/\\n/g'
```

---

## How to Run

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt**:
```
fastapi
uvicorn
python-dotenv
pydantic
google-adk
google-genai
requests
PyJWT
cryptography
```

### 2. Set Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Google AI
GOOGLE_API_KEY=your_gemini_api_key

# Gmail (Required)
GMAIL_ADDRESS=bot@company.com
GMAIL_APP_PASSWORD=your_app_password

# Jira & Confluence (Required)
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_EMAIL=admin@company.com
JIRA_API_TOKEN=your_atlassian_api_token

# Bitbucket (Separate token!)
BITBUCKET_USERNAME=your_atlassian_email@company.com
BITBUCKET_API_TOKEN=your_bitbucket_token
BITBUCKET_WORKSPACE=your-workspace

# GitHub (Optional)
GITHUB_ORG=your-org
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=your_private_key
GITHUB_INSTALLATION_ID=987654

# Email Polling (Optional)
EMAIL_POLL_ENABLED=true
EMAIL_POLL_INTERVAL=30
```

### 3. Run the Server

```bash
uvicorn access_controller_agent.server:app --reload --port 8000
```

Server starts with:
- Background email polling (if enabled)
- REST API on `http://localhost:8000`
- Health check at `http://localhost:8000/health`

### 4. Test Email Integration

**Send a test email** to `GMAIL_ADDRESS`:
```
Subject: Access request
Body: Please grant john@company.com Developer access to KAN project in Jira
```

**Watch logs**:
```
📧 Email polling started (interval: 30s)
📬 Found 1 unread email(s), checking for access requests...
  📧 Processing access request: Access request from admin@company.com
  ✅ Processed successfully
```

**Check your inbox** for threaded reply:
```
✓ Granted john@company.com Developer access to KAN project in Jira.
You can now create and edit issues.
```

### 5. Test REST API

```bash
# Direct request (non-email)
curl -X POST http://localhost:8000/request \
  -H "Content-Type: application/json" \
  -d '{"message": "Give sarah@co.com write access to ENG Confluence space"}'

# Manual email poll
curl -X POST http://localhost:8000/email/poll \
  -H "Content-Type: application/json" \
  -d '{"limit": 5, "auto_process": true}'

# View unread emails
curl http://localhost:8000/email/unread?limit=10
```

---

## Tech Stack

| Technology | Role |
|------------|------|
| **Google ADK** | Multi-agent orchestration (LlmAgent, Runner, InMemorySessionService) |
| **Gemini 2.0 Flash** | LLM for natural language understanding and task planning |
| **FastAPI** | Async web server, REST API, background tasks |
| **Gmail IMAP/SMTP** | Email reading and sending (app password auth) |
| **Jira Cloud REST API v3** | Project role management, user lookup, groups |
| **Confluence Cloud REST API v2** | Space permissions, user access |
| **Bitbucket Cloud API 2.0** | Repository permissions, workspace management |
| **GitHub REST API** | Organization membership, repository collaborators, teams |
| **PyJWT + cryptography** | GitHub App authentication (JWT generation) |
| **Pydantic** | Request/response validation |
| **python-dotenv** | Environment variable loading |
| **Uvicorn** | ASGI server for FastAPI |
| **Python 3.9+** | Runtime |

---

## Project Structure

```
access_controller_agent/
├── server.py                       # FastAPI app + email polling
├── agent.py                        # Root agent (Coordinator)
├── tools.py                        # 70+ platform-specific tool functions
│
├── services/                       # (empty - services in root)
├── tools/                          # (empty - tools in root)
│
├── sub_agents/
│   ├── __init__.py
│   ├── jira_agent.py               # Jira specialist
│   ├── confluence_agent.py         # Confluence specialist
│   ├── bitbucket_agent.py          # Bitbucket specialist
│   ├── github_agent.py             # GitHub specialist
│   └── email_agent.py              # Email reply handler
│
├── jira_service.py                 # JiraService class
├── confluence_service.py           # ConfluenceService class
├── bitbucket_service.py            # BitbucketService + AtlassianAdminService
├── github_service.py               # GitHubService class (GitHub App auth)
├── email_service.py                # EmailService class (Gmail IMAP/SMTP)
│
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create manually)
├── .env.example                    # Environment template
├── README.md                       # Quick start guide
├── DOCUMENTATION.md                # This comprehensive guide
├── BITBUCKET_SETUP.md              # Bitbucket-specific instructions
└── SIMPLIFIED_SETUP.md             # Minimal setup guide
```

---

## Methodology

| Concern | Approach |
|---------|----------|
| **Email interface** | Gmail IMAP (read) + SMTP (send) with app password |
| **Email threading** | Extract Message-ID/References, construct In-Reply-To headers |
| **Email filtering** | Keyword matching + sender blacklist |
| **Agent orchestration** | Hierarchical ADK structure (Coordinator → Specialists) |
| **Intelligent defaults** | Context-aware role/permission inference (no permission asking) |
| **User auto-invitation** | Admin API + product APIs + auto-approval flow |
| **Multi-platform routing** | LLM-driven delegation based on keywords (jira, confluence, github) |
| **Background polling** | FastAPI lifespan + asyncio.create_task |
| **Session isolation** | UUID-based session IDs per email request |
| **Error handling** | Try/except at all layers, structured error dicts, user-friendly notifications |
| **Service abstraction** | Separate service classes per platform (API clients) |
| **Tool standardization** | All tools return `{status, ...}` dicts |
| **GitHub authentication** | GitHub App JWT + installation token (auto-refresh) |
| **Bitbucket authentication** | Scoped API token (separate from Atlassian token) |

---

## Hierarchical Multi-Agent Pattern

The **Hierarchical Multi-Agent** pattern enables **specialized expertise with centralized coordination**. Unlike flat agent systems where all agents have equal authority, this pattern creates a clear delegation hierarchy:

### Key Benefits

1. **Separation of Concerns**: Each sub-agent masters one domain (Jira expert ≠ GitHub expert)
2. **Centralized Logic**: Coordinator handles routing, context management, and response synthesis
3. **Scalability**: Add new platforms by adding new sub-agents (no coordinator changes)
4. **Testability**: Test each agent independently
5. **Maintainability**: Platform API changes only affect one sub-agent

### Google ADK Implementation

```python
# Root Coordinator
root_agent = LlmAgent(
    name="AccessControllerCoordinator",
    model=GEMINI_MODEL,
    description="Central coordinator...",
    instruction="""Route requests to specialists:
    - Jira mentions → JiraAgent
    - Confluence mentions → ConfluenceAgent
    - Always finish with EmailAgent""",
    # NO direct tools - only delegates
)

# Specialists (imported from sub_agents/)
from .sub_agents import (
    jira_agent,       # Has jira_* tools
    confluence_agent, # Has confluence_* tools
    bitbucket_agent,  # Has bitbucket_* tools
    github_agent,     # Has github_* tools
    email_agent       # Has email_* tools
)

# Coordinator delegates via LLM-driven "transfer to <agent>"
```

### Delegation Flow

1. **User email arrives** → Coordinator receives via `run_agent()`
2. **Coordinator parses intent**:
   - "Grant John Jira and Confluence access"
   - Action: grant
   - Platforms: Jira, Confluence
   - User: John
3. **Coordinator delegates**:
   - `"Transfer to JiraAgent to grant John access to KAN project"`
   - `"Transfer to ConfluenceAgent to grant John write access to ENG space"`
4. **Sub-agents execute**:
   - JiraAgent calls `jira_grant_access()`
   - ConfluenceAgent calls `confluence_grant_space_access()`
5. **Coordinator synthesizes**:
   - Collects results from both sub-agents
   - Generates unified response: "✓ Granted access to both platforms"
6. **Coordinator delegates to EmailAgent**:
   - `"Transfer to EmailAgent to send reply. Email ID: <id>. Message: <synthesized response>"`
7. **EmailAgent sends reply** maintaining thread

---

## Future Enhancements

- **Slack/Teams integration** — Support Slack DMs and Teams chat as input channels
- **Approval workflows** — Require manager approval for sensitive access grants
- **Audit logging** — Store all access changes in database for compliance
- **Access expiration** — Auto-revoke temporary access after N days
- **Bulk operations** — "Onboard team of 10 developers to project X"
- **Natural language queries** — "Who has admin access to KAN?" (complex reporting)
- **Custom rules engine** — JSON/YAML configuration for org-specific policies
- **Multi-org support** — Manage multiple Atlassian/GitHub organizations
- **Role-based agent access** — Restrict agents based on requester's role

---

## License

[Specify your license here]

## Contributing

[Specify contribution guidelines here]

## Support

For issues or questions:
- Open an issue on GitHub
- Contact: [your contact info]
