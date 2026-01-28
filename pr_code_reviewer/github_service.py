import os
import requests
from github import Github, GithubIntegration, Auth
from dotenv import load_dotenv

# Load env variables (likely loaded by server.py, but safe to re-load)
load_dotenv()

class GitHubService:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("Warning: GITHUB_TOKEN not found in environment.")
        self.client = Github(auth=Auth.Token(token)) if token else None
        
        # Verify connection immediately
        if self.client:
            try:
                user = self.client.get_user().login
                print(f"✅ GitHub Service connected as: {user}")
            except Exception as e:
                print(f"❌ GitHub Token Error: {e}")

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """
        Fetches the raw diff of a Pull Request.
        """
        if not self.client:
            return "Error: GitHub Client not initialized (Missing Token)."
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            # We specifically want the DIFF string, requesting via headers usually easiest for raw
            # However, PyGithub doesn't expose raw diff easily on the object.
            # We can use the diff_url with requests and the token.
            
            headers = {
                "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github.v3.diff"
            }
            response = requests.get(pr.url, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error fetching diff: {str(e)}"

    def post_comment(self, repo_name: str, pr_number: int, body: str):
        """
        Posts a comment on the PR.
        """
        if not self.client: return
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(body)
            print(f"Comment posted on PR #{pr_number}")
        except Exception as e:
            print(f"Failed to post comment: {e}")

    def set_status_check(self, repo_name: str, sha: str, state: str, description: str, context: str):
        """
        Sets a Commit Status (success, failure, pending).
        state: 'pending', 'success', 'error', 'failure'
        """
        if not self.client: return
        try:
            repo = self.client.get_repo(repo_name)
            commit = repo.get_commit(sha)
            if "403" in str(e):
                print("HINT: Your GitHub Token needs 'repo:status' (Classic) or 'Commit statuses: Read/Write' (Fine-grained) permissions.")
            commit.create_status(
                state=state,
                description=description[:140], # GitHub max length
                context=f"AI-Review/{context}"
            )
            print(f"Status '{state}' set for context '{context}'")
        except Exception as e:
            print(f"Failed to set status: {e}")
