import unittest
from unittest.mock import patch, MagicMock
from file_tools.rss_tools import parse_rss_feed

class TestRSSTools(unittest.TestCase):
    @patch('httpx.Client.get')
    def test_parse_rss_feed_success(self, mock_get):
        # Mocking the RSS feed content
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>Test Item 1</title>
                <link>http://example.com/1</link>
                <published>Wed, 12 Mar 2026 12:00:00 GMT</published>
            </item>
        </channel>
        </rss>"""
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = parse_rss_feed("http://example.com/rss")
        self.assertIn("Latest entries from Test Feed:", result)
        self.assertIn("Test Item 1", result)
        self.assertIn("http://example.com/1", result)

    @patch('httpx.Client.get')
    def test_parse_rss_feed_error(self, mock_get):
        mock_get.side_effect = Exception("Network Error")
        result = parse_rss_feed("http://example.com/rss")
        self.assertIn("Error parsing RSS feed: Network Error", result)

    @patch('file_tools.rss_tools.summarize_rss_entry')
    def test_summarize_rss_entry(self, mock_summarize):
        mock_summarize.return_value = "Summary of http://example.com/1:\n\nTest Content..."
        result = mock_summarize("http://example.com/1")
        self.assertIn("Summary of http://example.com/1:", result)
        self.assertIn("Test Content...", result)

if __name__ == '__main__':
    unittest.main()
