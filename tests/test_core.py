import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the agent root directory to the path so we can import modules
agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

class TestAgentCore(unittest.TestCase):
    def test_imports_and_syntax(self):
        """
        Ensures the core agent loop compiles and contains necessary functions.
        """
        try:
            import loop
            self.assertTrue(hasattr(loop, 'main'), "loop.py must have a main() function")
            self.assertTrue(hasattr(loop, 'execute_command'), "loop.py must have execute_command()")
            self.assertTrue(hasattr(loop, 'read_file'), "loop.py must have read_file()")
            self.assertTrue(hasattr(loop, 'write_file'), "loop.py must have write_file()")
        except Exception as e:
            self.fail(f"Failed to import loop.py. Syntax error or broken import. Error: {e}")

    @patch('subprocess.run')
    def test_execute_command_safe(self, mock_subprocess):
        """
        Test that execute_command returns a formatted string and handles outputs.
        """
        import loop
        # Setup mock return value
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Test Output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = loop.execute_command("echo 'Hello'")
        self.assertIn("Exit Code: 0", result)
        self.assertIn("Test Output", result)

if __name__ == '__main__':
    unittest.main()
