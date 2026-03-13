import unittest
import os
import sys
from file_tools.ast_tools import analyze_python_file, summarize_project, find_definition

class TestASTTools(unittest.TestCase):
    def setUp(self):
        # Set environment for tool resolution
        self.agent_root = os.getcwd()
        os.environ["AGENT_ROOT"] = self.agent_root

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

    def test_analyze_python_file_async(self):
        test_file = "temp_async.py"
        with open(test_file, "w") as f:
            f.write("async def async_func():\n    pass\n")
        try:
            res = analyze_python_file(test_file)
            self.assertIn("[ASYNC FUNC] async_func", res)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_analyze_python_file_class(self):
        test_file = "temp_class.py"
        with open(test_file, "w") as f:
            f.write("class MyClass:\n    \"\"\"My docstring\"\"\"\n    def my_method(self, arg1):\n        pass\n")
        try:
            res = analyze_python_file(test_file)
            self.assertIn("[CLASS] MyClass", res)
            self.assertIn("Doc: My docstring", res)
            self.assertIn("[METHOD] my_method(arg1)", res)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_analyze_python_file_assign(self):
        test_file = "temp_assign.py"
        with open(test_file, "w") as f:
            f.write("MY_CONST = 10\n")
        try:
            res = analyze_python_file(test_file)
            self.assertIn("[CONST/VAR] MY_CONST", res)
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

if __name__ == '__main__':
    unittest.main()
