import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the agent root directory to the path so we can import modules
agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

from file_tools.reporting_tools import generate_status_report, run_test_suite

class TestReportingTools(unittest.TestCase):
    @patch('subprocess.run')
    def test_run_test_suite(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Ran 67 tests in 9.272s\nOK"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_test_suite()
        self.assertIn("Test Suite: PASSED", result)
        self.assertIn("Ran 67 tests", result)
    @patch('file_tools.reporting_tools.get_usage')
    @patch('file_tools.reporting_tools.list_tasks')
    @patch('file_tools.reporting_tools.git_status')
    @patch('file_tools.reporting_tools.check_code_health')
    @patch('file_tools.reporting_tools.load_memory')
    @patch('file_tools.reporting_tools.run_test_suite')
    @patch('file_tools.reporting_tools.get_resource_summary')
    def test_generate_status_report(self, mock_res, mock_run_test, mock_load, mock_health, mock_git, mock_tasks, mock_usage):
        mock_usage.return_value = "API usage: OK"
        mock_tasks.return_value = "Tasks: OK"
        mock_git.return_value = "Git: OK"
        mock_health.return_value = "Health: OK"
        mock_load.return_value = {"entries": [{"metadata": {"tags": ["status"]}, "text": "entry 1"}]}
        mock_run_test.return_value = "Tests: OK"
        mock_res.return_value = "Resources: OK"
        
        report = generate_status_report()
        self.assertIn("# Hoshi Status Report", report)
        self.assertIn("API usage: OK", report)
        self.assertIn("Tasks: OK", report)
        self.assertIn("Git: OK", report)
        self.assertIn("Health: OK", report)
        self.assertIn("entry 1", report)

if __name__ == '__main__':
    unittest.main()
