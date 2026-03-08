import unittest
import os
import sys

# Add the agent root directory to the path so we can import modules
agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

import file_tools.tools as tools

class TestRunPython(unittest.TestCase):
    def test_run_python_success(self):
        code = "print('Hello, World!')\nx = 5\nprint(x)"
        result = tools.run_python(code)
        self.assertIn("Hello, World!", result)
        self.assertIn("5", result)
        
    def test_run_python_syntax_error(self):
        code = "print('Hello, World!'\n"
        result = tools.run_python(code)
        self.assertIn("SyntaxError", result)
        
    def test_run_python_exception(self):
        code = "x = 1 / 0"
        result = tools.run_python(code)
        self.assertIn("ZeroDivisionError", result)

if __name__ == '__main__':
    unittest.main()
