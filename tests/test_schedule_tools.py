import unittest
import os
import json
from file_tools.schedule_tools import add_scheduled_task, list_scheduled_tasks, remove_scheduled_task, check_and_trigger_scheduled_tasks, _load_schedule, SCHEDULE_FILE

class TestScheduleTools(unittest.TestCase):
    def setUp(self):
        if os.path.exists(SCHEDULE_FILE):
            os.remove(SCHEDULE_FILE)
            
    def tearDown(self):
        if os.path.exists(SCHEDULE_FILE):
            os.remove(SCHEDULE_FILE)
            
    def test_add_scheduled_task(self):
        res = add_scheduled_task("Test task", interval_seconds=10)
        self.assertIn("added", res)
        schedule = _load_schedule()
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0]["description"], "Test task")
        self.assertEqual(schedule[0]["interval_seconds"], 10)
        
    def test_remove_scheduled_task(self):
        add_scheduled_task("Task 1", interval_seconds=10)
        add_scheduled_task("Task 2", interval_seconds=20)
        schedule = _load_schedule()
        self.assertEqual(len(schedule), 2)
        
        task_id = schedule[0]["id"]
        res = remove_scheduled_task(task_id)
        self.assertIn("removed", res)
        
        schedule = _load_schedule()
        self.assertEqual(len(schedule), 1)
        self.assertEqual(schedule[0]["description"], "Task 2")

    def test_list_scheduled_tasks(self):
        add_scheduled_task("Task 1", interval_seconds=10)
        res = list_scheduled_tasks()
        self.assertIn("Task 1", res)
        self.assertIn("Interval: 10", res)
        
if __name__ == '__main__':
    unittest.main()
