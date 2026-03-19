import unittest
import os
import json
import shutil
from file_tools.tools import save_memory, load_memory, search_memory, add_memory_entry

class TestMemory(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_memory_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.memory_file = os.path.join(self.test_dir, "long_term_memory.json")
        
        # Override AGENT_ROOT for testing
        self.old_agent_root = os.environ.get("AGENT_ROOT")
        os.environ["AGENT_ROOT"] = os.path.realpath(self.test_dir)
        
        if os.path.exists(self.memory_file):
            os.remove(self.memory_file)

    def tearDown(self):
        # Restore AGENT_ROOT
        if self.old_agent_root:
            os.environ["AGENT_ROOT"] = self.old_agent_root
        else:
            del os.environ["AGENT_ROOT"]
            
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

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
        # Context might not be returned if similarity is high enough or depending on implementation
        # But let's check if the entry itself is there
        self.assertIn("ENTRY: Target memory: My name is Hoshi.", search_result)

    def test_search_memory_no_entries(self):
        result = search_memory("test")
        self.assertEqual(result, "No memory entries found.")

    def test_add_memory_entry_with_metadata(self):
        metadata = {"date": "2026-03-12", "type": "test"}
        result = add_memory_entry("Test message", metadata=metadata)
        self.assertIn("Added", result)
        
        memory = load_memory()
        self.assertIn("entries", memory)
        self.assertEqual(memory["entries"][-1]["metadata"]["date"], "2026-03-12")

    def test_search_memory_threshold_and_filter(self):
        add_memory_entry("Important data about project A.", metadata={"project": "A"})
        add_memory_entry("Irrelevant fluff about project B.", metadata={"project": "B"})
        
        # Test threshold
        result = search_memory("Important project A", threshold=0.1)
        self.assertIn("ENTRY: Important data about project A.", result)
        
        # Test metadata filter
        result = search_memory("project", metadata_filter={"project": "B"})
        self.assertIn("ENTRY: Irrelevant fluff about project B.", result)
        self.assertNotIn("ENTRY: Important data about project A.", result)

    def test_save_memory_invalid_data(self):
        result = save_memory("not a dict")
        self.assertIn("Error: Memory data must be a dictionary.", result)

if __name__ == '__main__':
    unittest.main()
