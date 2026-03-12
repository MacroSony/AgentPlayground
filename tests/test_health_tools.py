import unittest
import os
import shutil
from file_tools.health_tools import check_code_health

class TestHealthTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = "temp_health_test"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_code_health_markers(self):
        test_file = os.path.join(self.test_dir, "markers.py")
        print(f"\nDEBUG: Creating {test_file}")
        with open(test_file, "w") as f:
            f.write("# TODO: Fix this\n")
            f.write("# FIXME: Urgent bug\n")
        
        print(f"DEBUG: File exists: {os.path.exists(test_file)}")
        result = check_code_health(self.test_dir)
        print(f"DEBUG: Result: {result}")
        self.assertIn("TODO: Fix this", result)
        self.assertIn("FIXME: Urgent bug", result)

    def test_check_code_health_issues(self):
        test_file = os.path.join(self.test_dir, "issues.py")
        with open(test_file, "w") as f:
            f.write("try:\n    pass\nexcept:\n    pass\n") # Bare except
            f.write("eval('1+1')\n") # Unsafe call
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

if __name__ == '__main__':
    unittest.main()
