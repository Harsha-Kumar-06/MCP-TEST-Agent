import os
import re
import logging
import requests
from github import Github, GithubIntegration, Auth
from dotenv import load_dotenv

# Load env variables (likely loaded by server.py, but safe to re-load)
load_dotenv()

logger = logging.getLogger("GitHubService")

class GitHubService:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            logger.warning("Warning: GITHUB_TOKEN not found in environment.")
        self.client = Github(auth=Auth.Token(token)) if token else None
        
        # Verify connection immediately
        if self.client:
            try:
                user = self.client.get_user().login
                logger.info(f"✅ GitHub Service connected as: {user}")
            except Exception as e:
                logger.error(f"❌ GitHub Token Error: {e}")

    def get_pr_metadata(self, repo_name: str, pr_number: int) -> dict:
        """
        Fetches and logs detailed PR metadata.
        """
        if not self.client:
            logger.error("GitHub Client not initialized")
            return {}
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Fetch changed files with stats
            files = list(pr.get_files())
            
            logger.info("="*80)
            logger.info("📋 PR METADATA")
            logger.info("="*80)
            logger.info(f"Title: {pr.title}")
            logger.info(f"Description: {pr.body[:200] if pr.body else 'No description'}...")
            logger.info(f"State: {pr.state.upper()}")
            logger.info(f"Author: {pr.user.login}")
            logger.info(f"Created: {pr.created_at}")
            logger.info(f"Updated: {pr.updated_at}")
            logger.info(f"Base: {pr.base.ref} (SHA: {pr.base.sha[:8]})")
            logger.info(f"Head: {pr.head.ref} (SHA: {pr.head.sha[:8]})")
            logger.info(f"")
            logger.info(f"📊 STATISTICS")
            logger.info(f"Commits: {pr.commits}")
            logger.info(f"Files Changed: {pr.changed_files}")
            logger.info(f"Additions: +{pr.additions}")
            logger.info(f"Deletions: -{pr.deletions}")
            logger.info(f"Total Changes: {pr.additions + pr.deletions}")
            logger.info(f"")
            
            if pr.labels:
                labels = ", ".join([label.name for label in pr.labels])
                logger.info(f"🏷️  Labels: {labels}")
            
            if pr.requested_reviewers:
                reviewers = ", ".join([r.login for r in pr.requested_reviewers])
                logger.info(f"👥 Requested Reviewers: {reviewers}")
            
            logger.info(f"")
            logger.info("📁 CHANGED FILES")
            logger.info("-"*80)
            
            for file in files:
                status_emoji = {
                    "added": "➕",
                    "modified": "📝",
                    "removed": "❌",
                    "renamed": "🔄"
                }.get(file.status, "📄")
                
                logger.info(f"{status_emoji} {file.filename}")
                logger.info(f"   Status: {file.status}")
                logger.info(f"   Changes: +{file.additions} -{file.deletions} (total: {file.changes})")
                if file.patch:
                    patch_lines = len(file.patch.split('\n'))
                    logger.info(f"   Patch: {patch_lines} lines")
            
            logger.info("="*80)
            
            return {
                "title": pr.title,
                "author": pr.user.login,
                "files_changed": pr.changed_files,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "files": [{
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "changes": f.changes
                } for f in files]
            }
        except Exception as e:
            logger.error(f"Error fetching PR metadata: {e}")
            return {}

    def get_pr_diff(self, repo_name: str, pr_number: int) -> str:
        """
        Fetches the raw diff of a Pull Request and logs parsed information.
        """
        if not self.client:
            return "Error: GitHub Client not initialized (Missing Token)."
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Fetch the raw diff
            headers = {
                "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github.v3.diff"
            }
            response = requests.get(pr.url, headers=headers)
            response.raise_for_status()
            diff_text = response.text
            
            # Parse and log diff structure
            self._parse_and_log_diff(diff_text)
            
            return diff_text
        except Exception as e:
            logger.error(f"Error fetching diff: {e}")
            return f"Error fetching diff: {str(e)}"
    
    def _parse_and_log_diff(self, diff_text: str):
        """
        Parses the diff text and logs information about changed files.
        """
        logger.info("")
        logger.info("="*80)
        logger.info("📝 DIFF CONTENT ANALYSIS")
        logger.info("="*80)
        
        # Split diff by file
        file_diffs = re.split(r'^diff --git ', diff_text, flags=re.MULTILINE)
        file_diffs = [d for d in file_diffs if d.strip()]
        
        logger.info(f"Total files in diff: {len(file_diffs)}")
        logger.info("")
        
        for i, file_diff in enumerate(file_diffs, 1):
            # Extract filename
            filename_match = re.search(r'^a/(.+?) b/(.+?)$', file_diff, re.MULTILINE)
            if filename_match:
                old_file = filename_match.group(1)
                new_file = filename_match.group(2)
                
                # Count additions and deletions
                additions = len(re.findall(r'^\+(?!\+\+)', file_diff, re.MULTILINE))
                deletions = len(re.findall(r'^-(?!--)', file_diff, re.MULTILINE))
                
                # Detect file status
                if 'new file mode' in file_diff:
                    status = "➕ ADDED"
                elif 'deleted file mode' in file_diff:
                    status = "❌ DELETED"
                elif 'rename from' in file_diff:
                    status = "🔄 RENAMED"
                else:
                    status = "📝 MODIFIED"
                
                logger.info(f"{i}. {status}: {new_file}")
                logger.info(f"   +{additions} -{deletions} lines")
                
                # Show a preview of changes (first few lines)
                lines = file_diff.split('\n')
                change_lines = [l for l in lines if l.startswith('+') or l.startswith('-')][:3]
                if change_lines:
                    logger.info(f"   Preview:")
                    for line in change_lines:
                        logger.info(f"     {line[:80]}")
                logger.info("")
        
        logger.info("="*80)

    def post_comment(self, repo_name: str, pr_number: int, body: str):
        """
        Posts a comment on the PR.
        """
        if not self.client: return
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(body)
            logger.info(f"💬 Comment posted on PR #{pr_number}")
        except Exception as e:
            logger.error(f"Failed to post comment: {e}")

    def set_status_check(self, repo_name: str, sha: str, state: str, description: str, context: str):
        """
        Sets a Commit Status (success, failure, pending).
        state: 'pending', 'success', 'error', 'failure'
        """
        if not self.client: return
        try:
            repo = self.client.get_repo(repo_name)
            commit = repo.get_commit(sha)
            commit.create_status(
                state=state,
                description=description[:140], # GitHub max length
                context=f"AI-Review/{context}"
            )
            logger.info(f"✓ Status '{state}' set for context '{context}'")
        except Exception as e:
            if "403" in str(e):
                logger.error("HINT: Your GitHub Token needs 'repo:status' (Classic) or 'Commit statuses: Read/Write' (Fine-grained) permissions.")
            logger.error(f"Failed to set status: {e}")
