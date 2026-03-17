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
        self.assertIn("CONTEXT [-1]: First memory.", search_result)
        self.assertIn("CONTEXT [1]: Third memory.", search_result)

    def test_search_memory_no_entries(self):
        result = search_memory("test")
        self.assertEqual(result, "No memory entries found.")

    def test_add_memory_entry_with_metadata(self):
        metadata = {"date": "2026-03-12", "type": "test"}
        result = add_memory_entry("Test message", metadata=metadata)
        self.assertIn("Added", result)
        
        memory = load_memory()
        self.assertIn("entries", memory)
        self.assertEqual(memory["entries"][-1]["metadata"], metadata)

    def test_search_memory_threshold_and_filter(self):
        add_memory_entry("Important data about project A.", metadata={"project": "A"})
        add_memory_entry("Irrelevant fluff about project B.", metadata={"project": "B"})
        
        # Test threshold
        result = search_memory("Important project A", threshold=0.5)
        self.assertIn("ENTRY: Important data about project A.", result)
        
        # Keyword search with tokens 'important', 'project', 'a' 
        # matches exactly those 3 in the entry. So score is 1.0.
        # We need a query that only partially matches to test threshold.
        result = search_memory("Very Important project A", threshold=0.9) 
        # The tool returns "No memory entries found for query: ..." or "No memory entries found above threshold ..."
        self.assertTrue("No memory entries found" in result)

        # Test metadata filter
        result = search_memory("project", metadata_filter={"project": "B"})
        self.assertIn("ENTRY: Irrelevant fluff about project B.", result)
        self.assertNotIn("ENTRY: Important data about project A.", result)

    def test_save_memory_invalid_data(self):
        result = save_memory("not a dict")
        self.assertIn("Error: Memory data must be a dictionary.", result)

    def test_add_memory_entry_auto_tag(self):
        msg = "This is a git commit message for a task"
        res = add_memory_entry(msg, auto_tag=True)
        # The result string includes text[:100]
        self.assertIn("Added", res)
        self.assertIn("'git'", res)
        self.assertIn("'task'", res)
        
        memory = load_memory()
        tags = memory["entries"][-1]["metadata"]["tags"]
        self.assertIn("git", tags)
        self.assertIn("task", tags)

if __name__ == '__main__':
    unittest.main()
