import unittest
import os
import sys
from file_tools.ast_tools import analyze_python_file, summarize_project, find_definition

class TestASTTools(unittest.TestCase):
    def test_analyze_python_file(self):
        res = analyze_python_file("file_tools/ast_tools.py")
        self.assertIn("[FUNC] analyze_python_file", res)
        self.assertIn("[FUNC] summarize_project", res)
        self.assertIn("[FUNC] find_definition", res)

    def test_summarize_project(self):
        res = summarize_project()
        self.assertIn("--- loop.py ---", res)
        self.assertIn("--- file_tools/tools.py ---", res)

    def test_find_definition(self):
        res = find_definition("send_discord_message")
        self.assertIn("Function 'send_discord_message' found in file_tools/tools.py", res)
        
        res = find_definition("NonExistentFunctionXYZ")
        self.assertEqual(res, "No definition found for 'NonExistentFunctionXYZ'.")

if __name__ == '__main__':
    unittest.main()
