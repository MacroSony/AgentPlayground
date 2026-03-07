import unittest
import os
from loop import save_memory, load_memory

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.memory_file = "long_term_memory.json"
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def tearDown(self):
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def test_save_and_load_memory(self):
        # Initial load should return an empty dict or default
        memory = load_memory()
        self.assertEqual(memory, {})

        # Save some data
        save_memory({"test_key": "test_value"})

        # Load and verify
        memory = load_memory()
        self.assertEqual(memory, {"test_key": "test_value"})

if __name__ == '__main__':
    unittest.main()
