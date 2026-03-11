import unittest
import os
import sys
import shutil

# Ensure agent root is in path
agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)

from file_tools.tools import patch_file

class TestPatchFile(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(agent_dir, "test_workspace_patch")
        os.makedirs(self.test_dir, exist_ok=True)
        # Mock AGENT_ROOT for resolve_safe_path
        self.old_agent_root = os.environ.get('AGENT_ROOT')
        os.environ['AGENT_ROOT'] = self.test_dir
        
        self.test_file = os.path.join(self.test_dir, "test.txt")
        with open(self.test_file, "w") as f:
            f.write("Line 1\nLine 2\nLine 3\n")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if self.old_agent_root:
            os.environ['AGENT_ROOT'] = self.old_agent_root
        else:
            del os.environ['AGENT_ROOT']

    def test_patch_file_success(self):
        patches = """
<<<<<<< SEARCH
Line 2
=======
Line Two (Updated)
>>>>>>> REPLACE
"""
        result = patch_file("test.txt", patches)
        self.assertIn("Successfully applied 1 patch(es)", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "Line 1\nLine Two (Updated)\nLine 3\n")

    def test_patch_file_multi_block(self):
        patches = """
<<<<<<< SEARCH
Line 1
=======
First Line
>>>>>>> REPLACE
<<<<<<< SEARCH
Line 3
=======
Last Line
>>>>>>> REPLACE
"""
        result = patch_file("test.txt", patches)
        self.assertIn("Successfully applied 2 patch(es)", result)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "First Line\nLine 2\nLast Line\n")

    def test_patch_file_not_found(self):
        patches = """
<<<<<<< SEARCH
Nonexistent
=======
Whatever
>>>>>>> REPLACE
"""
        result = patch_file("test.txt", patches)
        self.assertIn("Error: SEARCH block not found", result)

if __name__ == '__main__':
    unittest.main()
