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
        self.assertIn("Syntax Error", result)
        
    def test_run_python_exception(self):
        code = "x = 1 / 0"
        result = tools.run_python(code)
        self.assertIn("ZeroDivisionError", result)

    def test_run_python_memory_limit(self):
        # Try to allocate 100MB while limit is 50MB
        code = "import time; l = [0] * (20 * 1024 * 1024)"
        result = tools.run_python(code, memory_limit_mb=50)
        self.assertTrue("killed due to resource limits" in result.lower() or "memoryerror" in result.lower())

    def test_run_python_cpu_limit(self):
        code = "import time; start = time.time();\nwhile time.time() - start < 10: pass"
        result = tools.run_python(code, timeout=1)
        # SIGXCPU is code -24 or sometimes -9 depending on environment
        self.assertTrue("killed due to" in result.lower() or "exit code" in result.lower())

if __name__ == '__main__':
    unittest.main()
