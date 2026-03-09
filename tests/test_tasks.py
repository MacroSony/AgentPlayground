import unittest
import os
import sys
import json

agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if agent_dir not in sys.path:
    sys.path.append(agent_dir)

from file_tools.tasks import add_task, list_tasks, update_task_status

class TestTasks(unittest.TestCase):
    def setUp(self):
        self.tasks_file = os.path.join(agent_dir, "tasks.json")
        if os.path.exists(self.tasks_file):
            os.remove(self.tasks_file)

    def tearDown(self):
        if os.path.exists(self.tasks_file):
            os.remove(self.tasks_file)

    def test_add_task(self):
        result = add_task("Test task 1")
        self.assertIn("Task added", result)
        
        with open(self.tasks_file, "r") as f:
            tasks = json.load(f)
        
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["description"], "Test task 1")
        self.assertEqual(tasks[0]["status"], "todo")

    def test_list_tasks(self):
        add_task("First task")
        add_task("Second task")
        
        result = list_tasks()
        self.assertIn("[1] [TODO] First task", result)
        self.assertIn("[2] [TODO] Second task", result)

    def test_update_task_status(self):
        add_task("Task to update")
        
        result = update_task_status(1, "done")
        self.assertIn("status updated to 'done'", result)
        
        with open(self.tasks_file, "r") as f:
            tasks = json.load(f)
            
        self.assertEqual(tasks[0]["status"], "done")

    def test_update_task_not_found(self):
        result = update_task_status(999, "done")
        self.assertIn("not found", result)

if __name__ == '__main__':
    unittest.main()
