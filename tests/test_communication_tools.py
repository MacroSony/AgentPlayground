import unittest
import os
from file_tools.communication_tools import reply_to_user

class TestCommunicationTools(unittest.TestCase):
    def setUp(self):
        self.chat_log = os.path.join(os.getenv("AGENT_ROOT", os.getcwd()), "chat_log.txt")
        if os.path.exists(self.chat_log):
            os.remove(self.chat_log)

    def test_reply_to_user(self):
        result = reply_to_user("Hello user!")
        self.assertEqual(result, "Reply sent successfully.")
        self.assertTrue(os.path.exists(self.chat_log))
        with open(self.chat_log, "r") as f:
            content = f.read()
            self.assertIn("Hoshi: Hello user!", content)
            
    def tearDown(self):
        if os.path.exists(self.chat_log):
            os.remove(self.chat_log)

if __name__ == "__main__":
    unittest.main()