import unittest
from unittest.mock import patch, MagicMock
from file_tools.git_tools import git_status, git_checkout, git_commit, git_push, git_pull, _run_git

class TestGitTools(unittest.TestCase):

    @patch("file_tools.git_tools.subprocess.run")
    def test_run_git_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "On branch main"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = _run_git(["status"])
        self.assertIn("Exit Code: 0", result)
        self.assertIn("On branch main", result)

    @patch("file_tools.git_tools.subprocess.run")
    def test_run_git_error(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error: pathspec 'nonexistent' did not match any file(s) known to git"
        mock_run.return_value = mock_result

        result = _run_git(["checkout", "nonexistent"])
        self.assertIn("Exit Code: 1", result)
        self.assertIn("error: pathspec", result)

    @patch("file_tools.git_tools._run_git")
    def test_git_status(self, mock_run_git):
        mock_run_git.return_value = "Exit Code: 0\nOn branch main"
        self.assertEqual(git_status(), "Exit Code: 0\nOn branch main")
        mock_run_git.assert_called_with(["status"])

    @patch("file_tools.git_tools._run_git")
    def test_git_checkout(self, mock_run_git):
        git_checkout("feature-branch")
        mock_run_git.assert_called_with(["checkout", "feature-branch"])

        git_checkout("new-branch", create_new=True)
        mock_run_git.assert_called_with(["checkout", "-b", "new-branch"])

    @patch("file_tools.git_tools._run_git")
    def test_git_commit(self, mock_run_git):
        # Successful add and commit
        mock_run_git.side_effect = ["Exit Code: 0", "Exit Code: 0\n[main 1234abc] Test commit"]
        res = git_commit("Test commit")
        self.assertEqual(mock_run_git.call_count, 2)
        mock_run_git.assert_any_call(["add", "."])
        mock_run_git.assert_any_call(["commit", "-m", "Test commit"])
        self.assertIn("1234abc", res)

        # Failed add
        mock_run_git.reset_mock()
        mock_run_git.side_effect = ["Exit Code: 1\nFatal error", ""]
        res = git_commit("Test commit")
        self.assertEqual(mock_run_git.call_count, 1)
        self.assertIn("Failed to add files", res)

    @patch("file_tools.git_tools._run_git")
    def test_git_push(self, mock_run_git):
        git_push("feature-branch")
        mock_run_git.assert_called_with(["push", "origin", "feature-branch"])

        git_push()
        mock_run_git.assert_called_with(["push", "origin", "HEAD"])

    @patch("file_tools.git_tools._run_git")
    def test_git_pull(self, mock_run_git):
        git_pull("main")
        mock_run_git.assert_called_with(["pull", "origin", "main"])

if __name__ == '__main__':
    unittest.main()
