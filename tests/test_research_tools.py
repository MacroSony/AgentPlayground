import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from file_tools.research_tools import deep_search

class TestResearchTools(unittest.TestCase):

    @patch('google.genai.Client')
    @patch('file_tools.research_tools.search_web')
    @patch('file_tools.research_tools.fetch_url')
    @patch('file_tools.research_tools.add_memory_entry')
    def test_deep_search_success(self, mock_add_memory, mock_fetch, mock_search, mock_genai_client):
        # Mocking the client and its responses
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        # Mock sub-query generation
        mock_resp_subqueries = MagicMock()
        mock_resp_subqueries.text = json.dumps(["sub query 1"])
        
        # Mock summary generation
        mock_resp_summary = MagicMock()
        mock_resp_summary.text = "This is a summary."
        
        # Mock final synthesis
        mock_resp_final = MagicMock()
        mock_resp_final.text = "Final detailed report."
        
        mock_client.models.generate_content.side_effect = [
            mock_resp_subqueries,
            mock_resp_summary,
            mock_resp_final
        ]
        
        # Mock search_web
        mock_search.return_value = "Title: Result\nURL: http://example.com\nSnippet: info"
        
        # Mock fetch_url
        mock_fetch.return_value = "Cleaned web content."
        
        # Run the tool
        result = deep_search("test query", breadths=1)
        
        # Verify
        self.assertEqual(result, "Final detailed report.")
        self.assertTrue(mock_search.called)
        self.assertTrue(mock_fetch.called)
        self.assertTrue(mock_add_memory.called)

    def test_deep_search_exception(self):
        with patch('google.genai.Client', side_effect=Exception("API Error")):
            result = deep_search("test query")
            self.assertIn("Error during deep search: API Error", result)

if __name__ == "__main__":
    unittest.main()
