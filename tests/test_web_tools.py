import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock

# Since the tools are now in file_tools/tools.py, import them from there.
from file_tools.tools import fetch_url

class TestWebTools(unittest.TestCase):
    @patch('file_tools.tools.httpx.Client.get')
    def test_fetch_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Test Page</h1><p>Content.</p><script>console.log('test');</script></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Need to mock the context manager
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__.return_value = mock_client_instance
        
        with patch('file_tools.tools.httpx.Client', return_value=mock_client_instance):
            result = fetch_url("http://example.com")
            
        # Don't assert the actual HTML parsing if BeautifulSoup is not mocked correctly or available. 
        # But wait, it is available in .venv, we should just let it run.
        if "BeautifulSoup not installed" in result:
             self.skipTest("BeautifulSoup not installed")

        self.assertIn("Test Page", result)
        self.assertIn("Content.", result)
        self.assertNotIn("console.log", result)

    @patch('file_tools.tools.httpx.Client.get')
    def test_fetch_url_with_selector(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1 class='title'>Target Heading</h1><p>Exclude me.</p></body></html>"
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__.return_value = mock_client_instance
        
        with patch('file_tools.tools.httpx.Client', return_value=mock_client_instance):
            # Test selector match
            result = fetch_url("http://example.com", selector=".title")
            self.assertIn("Target Heading", result)
            self.assertNotIn("Exclude me.", result)
            
            # Test selector no match
            result_no_match = fetch_url("http://example.com", selector=".nonexistent")
            self.assertIn("Error: No elements for '.nonexistent'.", result_no_match)

            # Test remove_selectors
            result_remove = fetch_url("http://example.com", remove_selectors=[".title"])
            self.assertNotIn("Target Heading", result_remove)
            self.assertIn("Exclude me.", result_remove)

if __name__ == '__main__':
    unittest.main()
