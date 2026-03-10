import unittest
import os
import json
from file_tools.tools import save_memory, load_memory, search_memory, add_memory_entry

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.memory_file = "long_term_memory.json"
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def tearDown(self):
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def test_save_and_load_memory(self):
        memory = load_memory()
        self.assertEqual(memory, {})

        save_memory({"test_key": "test_value"})
        memory = load_memory()
        self.assertEqual(memory, {"test_key": "test_value"})

    def test_add_and_search_memory(self):
        # Adding a memory entry
        result = add_memory_entry("My name is Hoshi.")
        self.assertIn("Added memory entry", result)
        
        # Adding another
        add_memory_entry("I am an autonomous agent.")
        
        # Search memory
        search_result = search_memory("Who are you?")
        self.assertIn("Hoshi", search_result)
        self.assertIn("Score", search_result)

if __name__ == '__main__':
    unittest.main()
