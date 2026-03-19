import unittest
import os
import sys
import json
import shutil

# Ensure AGENT_ROOT is handled for isolation
class TestTasks(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.realpath("test_tasks_dir")
        os.makedirs(self.test_dir, exist_ok=True)
        self.tasks_file = os.path.join(self.test_dir, "tasks.json")
        
        self.old_agent_root = os.environ.get("AGENT_ROOT")
        os.environ["AGENT_ROOT"] = self.test_dir
        
        # We need to reload or re-import the module to ensure it picks up the new AGENT_ROOT
        # or rely on the fact that the functions call os.getenv each time.
        # Based on file_tools/tasks.py, TASKS_FILE is defined at module level.
        # This is the problem.
        
        import file_tools.tasks
        import importlib
        importlib.reload(file_tools.tasks)
        
        if os.path.exists(self.tasks_file):
            os.remove(self.tasks_file)

    def tearDown(self):
        if self.old_agent_root:
            os.environ["AGENT_ROOT"] = self.old_agent_root
        else:
            del os.environ["AGENT_ROOT"]
            
        import file_tools.tasks
        import importlib
        importlib.reload(file_tools.tasks)
            
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_task(self):
        from file_tools.tasks import add_task
        result = add_task("Test task 1")
        self.assertIn("Task added", result)
        
        with open(self.tasks_file, "r") as f:
            tasks = json.load(f)
        
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["description"], "Test task 1")
        self.assertEqual(tasks[0]["status"], "todo")

    def test_list_tasks(self):
        from file_tools.tasks import add_task, list_tasks
        add_task("First task")
        add_task("Second task")
        
        result = list_tasks()
        self.assertIn("[1] [TODO] First task", result)
        self.assertIn("[2] [TODO] Second task", result)

    def test_update_task_status(self):
        from file_tools.tasks import add_task, update_task_status
        add_task("Task to update")
        
        result = update_task_status(1, "done")
        self.assertIn("status updated to 'done'", result)
        
        with open(self.tasks_file, "r") as f:
            tasks = json.load(f)
            
        self.assertEqual(tasks[0]["status"], "done")

    def test_update_task_not_found(self):
        from file_tools.tasks import update_task_status
        result = update_task_status(999, "done")
        self.assertIn("not found", result)

if __name__ == '__main__':
    unittest.main()
