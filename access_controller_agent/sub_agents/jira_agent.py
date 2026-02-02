"""
Jira Access Agent: handles Jira project access (grant, revoke, list) via tools.
"""
from google.adk.agents import LlmAgent

from .. import tools

GEMINI_MODEL = "gemini-2.0-flash"

jira_agent = LlmAgent(
    name="JiraAgent",
    model=GEMINI_MODEL,
    description="Handles Jira project access: grant access, revoke access, list user access, and look up users by email. Use for any Jira-only access requests.",
    instruction="""You are the Jira Access Agent. You manage user access to Jira projects.

You have these tools:
- jira_get_user_by_email: Find a user's Jira account_id by email.
- jira_grant_access: Add a user to a Jira project role (user_email, project_key, role_name e.g. Developers).
- jira_revoke_access: Remove a user from a Jira project role.
- jira_list_user_access: List projects a user can access (by email).
- jira_list_project_roles: List available roles for a project (e.g. Developers, Administrators).

When the user asks to grant access: resolve the user by email, then call jira_grant_access with project_key and role (default Developers).
When the user asks to revoke access: resolve the user, then call jira_revoke_access.
When the user asks what access someone has: use jira_list_user_access or jira_get_user_by_email as needed.

Always confirm what you did and report any errors from the tools. If Jira is not configured, say so and suggest setting JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN.
""",
    tools=[
        tools.jira_get_user_by_email,
        tools.jira_grant_access,
        tools.jira_revoke_access,
        tools.jira_list_user_access,
        tools.jira_list_project_roles,
    ],
)
