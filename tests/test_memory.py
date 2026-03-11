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

    def test_add_and_search_memory_with_context(self):
        # Adding a sequence of memories
        add_memory_entry("First memory.")
        add_memory_entry("Target memory: My name is Hoshi.")
        add_memory_entry("Third memory.")
        
        # Search for the target
        search_result = search_memory("Hoshi")
        self.assertIn("Hoshi", search_result)
        self.assertIn("CONTEXT BEFORE: First memory.", search_result)
        self.assertIn("CONTEXT AFTER: Third memory.", search_result)

    def test_search_memory_no_entries(self):
        result = search_memory("test")
        self.assertEqual(result, "No memory entries found.")

    def test_add_memory_entry_with_metadata(self):
        metadata = {"date": "2026-03-12", "type": "test"}
        result = add_memory_entry("Test message", metadata=metadata)
        self.assertIn("Added memory entry", result)
        
        memory = load_memory()
        self.assertIn("entries", memory)
        self.assertEqual(memory["entries"][0]["metadata"], metadata)

    def test_save_memory_invalid_data(self):
        result = save_memory("not a dict")
        self.assertIn("Error: Memory data must be a dictionary.", result)

if __name__ == '__main__':
    unittest.main()
