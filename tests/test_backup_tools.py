import unittest
import os
import sys
import shutil
from file_tools.backup_tools import backup_data, list_backups, restore_data

class TestBackupTools(unittest.TestCase):
    def setUp(self):
        self.agent_root = os.getcwd()
        os.environ["AGENT_ROOT"] = self.agent_root
        self.backup_dir = os.path.join(self.agent_root, ".backups")
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)
            
    def tearDown(self):
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)

    def test_backup_and_list(self):
        res = backup_data()
        self.assertIn("Successfully created backup", res)
        
        list_res = list_backups()
        self.assertIn("Available Backups:", list_res)
        
    def test_restore(self):
        # Create a dummy file to backup
        dummy_file = os.path.join(self.agent_root, "dummy_test.txt")
        with open(dummy_file, "w") as f:
            f.write("test content")
            
        try:
            backup_data(extra_files=["dummy_test.txt"])
            backups = os.listdir(self.backup_dir)
            backup_name = backups[0]
            
            # Change the original file
            with open(dummy_file, "w") as f:
                f.write("changed content")
                
            # Restore
            res = restore_data(backup_name)
            self.assertIn("Successfully restored", res)
            
            with open(dummy_file, "r") as f:
                self.assertEqual(f.read(), "test content")
        finally:
            if os.path.exists(dummy_file):
                os.remove(dummy_file)

if __name__ == '__main__':
    unittest.main()
