import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.append(os.getcwd())

from file_tools.research_tools import deep_search

class TestResearchTools(unittest.TestCase):

    def _setup_mock_responses(self):
        mock_resp_subqueries = MagicMock()
        mock_resp_subqueries.text = json.dumps(["sub query 1"])
        
        mock_resp_summary = MagicMock()
        mock_resp_summary.text = "This is a summary."
        
        mock_resp_final = MagicMock()
        mock_resp_final.text = "Final detailed report."
        
        return mock_resp_summary, mock_resp_subqueries, mock_resp_final

    @patch('google.genai.Client')
    @patch('file_tools.research_tools.search_web')
    @patch('file_tools.research_tools.fetch_url')
    @patch('file_tools.research_tools.add_memory_entry')
    def test_deep_search_success(self, mock_add_memory, mock_fetch, mock_search, mock_genai_client):
        mock_client = MagicMock()
        mock_genai_client.return_value = mock_client
        
        mock_resp_summary, mock_resp_subqueries, mock_resp_final = self._setup_mock_responses()
        
        mock_client.models.generate_content.side_effect = [
            mock_resp_summary,
            mock_resp_subqueries,
            mock_resp_final
        ]
        
        mock_search.return_value = "Title: Result\nURL: http://example.com\nSnippet: info"
        mock_fetch.return_value = "Cleaned web content."
        
        result = deep_search("test query", max_depth=2, breadths=1)
        
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
