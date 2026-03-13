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
        
        # Mock sub-query generation (for depth 2, breath 1: depth 1 exploration, then refinement)
        mock_resp_subqueries = MagicMock()
        mock_resp_subqueries.text = json.dumps(["sub query 1"])
        
        # Mock summary generation (one per explored URL)
        mock_resp_summary = MagicMock()
        mock_resp_summary.text = "This is a summary."
        
        # Mock final synthesis
        mock_resp_final = MagicMock()
        mock_resp_final.text = "Final detailed report."
        
        # In this mock, search_web always returns http://example.com
        # Depth 1: 'test query' -> fetch -> Summary 1
        # Depth 1: Refinement 1 -> ["sub query 1"]
        # Depth 2: 'sub query 1' -> fetch (SKIPPED because URL already visited)
        # Depth 2: Refinement 2 -> ["sub query 1"]
        # Synthesis
        
        # Actually, deep_search uses _process_sub_query which calls generate_content for summary.
        # Then it calls _generate_sub_queries which calls generate_content for JSON.
        # Sequence:
        # 1. Depth 1: _process_sub_query('test query') -> Summary 1
        # 2. Depth 1: _generate_sub_queries('test query') -> Refinement 1
        # 3. Depth 2: _process_sub_query('sub query 1') -> (fetch skipped, NO generate_content)
        # 4. Depth 2: _generate_sub_queries('sub query 1') -> Refinement 2
        # 5. Synthesis -> Final
        
        # Let's count calls carefully:
        # Depth 1:
        #   - q='test query' -> _process_sub_query -> search_web -> fetch_url -> generate_content (SUMMARY) [Call 1]
        #   - depth=0 < 1 -> _generate_sub_queries -> generate_content (JSON) [Call 2]
        # Depth 2:
        #   - q='sub query 1' -> _process_sub_query -> search_web -> fetch_url -> (url in visited, NO generate_content)
        #   - depth=1 < 1 is FALSE -> loop ends
        # Synthesis -> generate_content [Call 3]
        
        mock_client.models.generate_content.side_effect = [
            mock_resp_summary,    # Call 1
            mock_resp_subqueries, # Call 2
            mock_resp_final       # Call 3
        ]
        
        # Mock search_web
        mock_search.return_value = "Title: Result\nURL: http://example.com\nSnippet: info"
        
        # Mock fetch_url
        mock_fetch.return_value = "Cleaned web content."
        
        # Run the tool with breadths=1 to match side_effect length
        # Depth 1: 1 query ('test query')
        # Depth 2: 1 query ('sub query 1')
        result = deep_search("test query", max_depth=2, breadths=1)
        
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
