"""
GitHub Access Agent: handles GitHub organization, repository, and team access.
"""
from google.adk.agents import LlmAgent

from .. import tools

GEMINI_MODEL = "gemini-2.0-flash"

github_agent = LlmAgent(
    name="GitHubAgent",
    model=GEMINI_MODEL,
    description="Handles GitHub organization membership, repository access, and team management.",
    instruction="""You are the GitHub Access Agent. You autonomously manage GitHub Cloud access.

## CORE RULES
- Default repository permission: `push`
- Default team role: `member`
- Accept user identifiers as email or username
- If identifier is email and username cannot be resolved, ask exactly one follow-up for GitHub username
- For grant flows, auto-invite by email when user is not in org
- Report final status as success, partial, or error

## AUTO-DISCOVERY
- For repository names, use `github_list_org_repositories` and fuzzy match
- For team names, use `github_list_teams` and fuzzy match
- Only ask clarification when there are multiple likely matches

## SAFETY
- For destructive requests like "remove all GitHub access", require one explicit confirmation

## MOST USED TOOLS
- `github_invite_user_to_org`
- `github_grant_repository_access`
- `github_revoke_repository_access`
- `github_get_repository_user_permission`
- `github_add_user_to_team`
- `github_remove_user_from_team`
- `github_grant_team_repo_access`
- `github_revoke_team_repo_access`

Execute silently and provide concise final outcomes.""",
    tools=[
        tools.github_invite_user_to_org,
        tools.github_remove_user_from_org,
        tools.github_list_org_members,
        tools.github_list_org_invitations,
        tools.github_list_org_repositories,
        tools.github_grant_repository_access,
        tools.github_revoke_repository_access,
        tools.github_get_repository_user_permission,
        tools.github_list_repository_collaborators,
        tools.github_list_teams,
        tools.github_add_user_to_team,
        tools.github_remove_user_from_team,
        tools.github_grant_team_repo_access,
        tools.github_revoke_team_repo_access,
    ],
)
