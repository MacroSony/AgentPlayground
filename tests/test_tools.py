import unittest
import os
import sys

# Add the agent root directory to the path so we can import modules
agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

class TestAgentTools(unittest.TestCase):
    def setUp(self):
        """Setup temporary test environment variables or files if needed."""
        self.test_dir = os.path.join(agent_dir, "test_workspace")
        os.makedirs(self.test_dir, exist_ok=True)
        # Mock AGENT_ROOT for tool safety checks
        os.environ['AGENT_ROOT'] = self.test_dir

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)
            
    def test_file_tools_sandbox(self):
        """
        Ensures read_file and write_file tools cannot escape the AGENT_ROOT.
        """
        import loop
        
        # Test safe write/read
        safe_file = "safe.txt"
        write_res = loop.write_file(safe_file, "safe content")
        self.assertIn("Successfully wrote", write_res)
        
        read_res = loop.read_file(safe_file)
        self.assertEqual(read_res, "safe content")

        # Test path traversal prevention
        unsafe_file = "../escaped.txt"
        write_res = loop.write_file(unsafe_file, "hack")
        self.assertIn("Error", write_res)
        self.assertIn("outside allowed root", write_res)

if __name__ == '__main__':
    unittest.main()
