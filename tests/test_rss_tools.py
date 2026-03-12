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
    def test_summarize_rss_entry_mock(self, mock_summarize):
        mock_summarize.return_value = "Summary of http://example.com/1:\n\nTest Content..."
        result = mock_summarize("http://example.com/1")
        self.assertIn("Summary of http://example.com/1:", result)
        self.assertIn("Test Content...", result)

    @patch('file_tools.tools.fetch_url')
    def test_summarize_rss_entry_real(self, mock_fetch):
        from file_tools.rss_tools import summarize_rss_entry
        mock_fetch.return_value = "A very long content string that needs to be summarized correctly by the tool."
        result = summarize_rss_entry("http://example.com/1")
        self.assertIn("Summary of http://example.com/1:", result)
        self.assertIn("A very long content", result)

    @patch('file_tools.tools.fetch_url')
    def test_summarize_rss_entry_error(self, mock_fetch):
        from file_tools.rss_tools import summarize_rss_entry
        mock_fetch.return_value = "Error: Failed to fetch URL"
        result = summarize_rss_entry("http://example.com/1")
        self.assertEqual(result, "Error: Failed to fetch URL")

if __name__ == '__main__':
    unittest.main()
