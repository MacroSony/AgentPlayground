import unittest
import os
import sys

sys.path.append(os.getenv("AGENT_ROOT", os.getcwd()))

class TestChatCli(unittest.TestCase):
    def test_imports(self):
        try:
            import chat
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"chat.py failed to import: {e}")

if __name__ == '__main__':
    unittest.main()
