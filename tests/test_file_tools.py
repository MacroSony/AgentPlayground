import unittest
import os
import sys

agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

from file_tools.tools import list_files, search_files, write_file, replace_in_file

class TestFileTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(agent_dir, "test_workspace_file_tools")
        os.makedirs(self.test_dir, exist_ok=True)
        os.environ['AGENT_ROOT'] = self.test_dir
        
        # Create some test files
        self.test_file_1 = os.path.join(self.test_dir, "file1.txt")
        self.test_file_2 = os.path.join(self.test_dir, "file2.txt")
        self.test_sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.test_sub_dir, exist_ok=True)
        self.test_file_3 = os.path.join(self.test_sub_dir, "file3.txt")
        
        with open(self.test_file_1, "w") as f:
            f.write("hello world")
        with open(self.test_file_2, "w") as f:
            f.write("foo bar")
        with open(self.test_file_3, "w") as f:
            f.write("hello again")

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.environ['AGENT_ROOT'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_list_files(self):
        result = list_files(self.test_dir)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)
        self.assertIn("subdir", result)
        
    def test_search_files(self):
        result = search_files(self.test_dir, "hello")
        self.assertIn("file1.txt", result)
        self.assertNotIn("file2.txt", result)
        self.assertIn("file3.txt", result)

    def test_search_files_regex(self):
        # Search for "hello" or "foo"
        result = search_files(self.test_dir, r"hello|foo", use_regex=True)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)
        self.assertIn("file3.txt", result)
        
    def test_search_files_invalid_regex(self):
        result = search_files(self.test_dir, r"(", use_regex=True)
        self.assertIn("Error: Invalid regex pattern", result)

    def test_search_files_not_found(self):
        result = search_files(self.test_dir, "nonexistent")
        self.assertIn("No files containing", result)

    def test_replace_in_file(self):
        result = replace_in_file(self.test_file_1, "world", "universe")
        self.assertIn("Successfully replaced", result)
        with open(self.test_file_1, "r") as f:
            content = f.read()
        self.assertEqual(content, "hello universe")

    def test_replace_in_file_not_found(self):
        result = replace_in_file(self.test_file_1, "nonexistent", "universe")
        self.assertIn("was not found in", result)

    def test_replace_in_file_empty_old_text(self):
        result = replace_in_file(self.test_file_1, "", "universe")
        self.assertIn("Error: old_text cannot be empty.", result)

    def test_write_and_read_file(self):
        from file_tools.tools import read_file
        test_path = "subdir/new_file.txt"
        content = "test content"
        write_result = write_file(test_path, content)
        self.assertIn("Successfully wrote to", write_result)
        
        read_result = read_file(test_path)
        self.assertEqual(read_result, content)

    def test_read_file_not_found(self):
        from file_tools.tools import read_file
        result = read_file("nonexistent_file.txt")
        self.assertIn("Error: File", result)
        self.assertIn("not found", result)

    def test_read_file_truncated(self):
        from file_tools.tools import read_file
        large_content = "a" * 20000
        write_file("large.txt", large_content)
        result = read_file("large.txt")
        self.assertTrue(len(result) < 20000)
        self.assertIn("CONTENT TRUNCATED", result)

    def test_resolve_safe_path_boundary(self):
        from file_tools.tools import resolve_safe_path
        # Should work
        path = resolve_safe_path("file1.txt")
        self.assertTrue(path.startswith(self.test_dir))
        
        # Should fail
        with self.assertRaises(ValueError):
            resolve_safe_path("../outside.txt")

    def test_list_files_invalid(self):
        result = list_files("nonexistent_dir")
        self.assertIn("Error: Path", result)
        self.assertIn("does not exist", result)

if __name__ == '__main__':
    unittest.main()
