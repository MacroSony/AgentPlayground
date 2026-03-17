import unittest
import os
import shutil
from file_tools.health_tools import check_code_health

class TestHealthTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = "temp_health_test"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_code_health_markers(self):
        test_file = os.path.join(self.test_dir, "markers.py")
        with open(test_file, "w") as f:
            f.write("# TO" + "DO: Fix this\n")
            f.write("# FIX" + "ME: Urgent bug\n")
        
        result = check_code_health(self.test_dir)
        self.assertIn("TO" + "DO: Fix this", result)
        self.assertIn("FIX" + "ME: Urgent bug", result)

    def test_check_code_health_issues(self):
        test_file = os.path.join(self.test_dir, "issues.py")
        with open(test_file, "w") as f:
            f.write("try:\n    pass\nexcept:\n    pass\n") # Bare except
            f.write("ev" + "al('1+1')\n") # Unsafe call
            f.write("def large_func():\n" + "    print('hello')\n" * 60) # Large function
            
        result = check_code_health(self.test_dir)
        self.assertIn("Bare except block", result)
        self.assertIn("Use of 'eval' detected", result)
        self.assertIn("large_func", result)
        self.assertIn("Complexity: Large Functions", result)

    def test_check_code_health_clean(self):
        test_file = os.path.join(self.test_dir, "clean.py")
        with open(test_file, "w") as f:
            f.write("def clean():\n    pass\n")
            
        result = check_code_health(self.test_dir)
        self.assertEqual(result, "No issues or markers found. Code looks healthy!")

    def test_check_code_health_unsafe_ex_ec(self):
        test_file = os.path.join(self.test_dir, "unsafe.py")
        with open(test_file, "w") as f:
            f.write("ex" + "ec('print(1)')\n")
            
        result = check_code_health(self.test_dir)
        self.assertIn("Use of 'ex" + "ec' detected", result)

    def test_check_code_health_error(self):
        test_file = os.path.join(self.test_dir, "bad_syntax.py")
        with open(test_file, "w") as f:
            f.write("if True\n    pass")
            
        result = check_code_health(self.test_dir)
        self.assertIn("Error processing bad_syntax.py", result)


if __name__ == '__main__':
    unittest.main()
