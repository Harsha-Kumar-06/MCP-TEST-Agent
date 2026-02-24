import unittest
from unittest.mock import patch

from access_controller_agent.github_service import GitHubService


class TestGitHubService(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "GITHUB_ORG": "acme",
            "GITHUB_APP_ID": "12345",
            "GITHUB_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----",
            "GITHUB_INSTALLATION_ID": "999",
        },
        clear=False,
    )
    def test_username_resolution(self):
        svc = GitHubService()
        self.assertTrue(svc.is_configured())
        res = svc.resolve_user_identifier("octocat")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["username"], "octocat")

    @patch.dict(
        "os.environ",
        {
            "GITHUB_ORG": "acme",
            "GITHUB_APP_ID": "12345",
            "GITHUB_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----",
            "GITHUB_INSTALLATION_ID": "999",
        },
        clear=False,
    )
    @patch("access_controller_agent.github_service.GitHubService.list_org_invitations")
    @patch("access_controller_agent.github_service.GitHubService.is_org_member")
    def test_email_resolution_pending_and_needs_username(self, mock_is_member, mock_invitations):
        svc = GitHubService()

        mock_invitations.return_value = {
            "status": "success",
            "invitations": [{"email": "dev@company.com"}],
        }
        mock_is_member.return_value = {"status": "success", "is_member": False}

        pending = svc.resolve_user_identifier("dev@company.com")
        self.assertEqual(pending["status"], "partial")
        self.assertTrue(pending["pending_invitation"])

        mock_invitations.return_value = {"status": "success", "invitations": []}
        unresolved = svc.resolve_user_identifier("unknown@company.com")
        self.assertEqual(unresolved["status"], "error")
        self.assertTrue(unresolved["needs_username"])


if __name__ == "__main__":
    unittest.main()
