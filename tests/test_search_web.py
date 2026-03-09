
import unittest
from unittest.mock import patch, MagicMock
from file_tools.tools import search_web

class TestSearchWeb(unittest.TestCase):
    @patch('file_tools.tools.httpx.Client')
    def test_search_web(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.text = '''
        <html><body>
        <div class="result">
            <a class="result__a" href="http://example.com/hoshiguma">Hoshiguma | Arknights Wiki</a>
            <a class="result__snippet">Hoshiguma is a 6-star Defender.</a>
            <a class="result__url" href="http://example.com/hoshiguma">example.com/hoshiguma</a>
        </div>
        </body></html>
        '''
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_class.return_value = mock_client_instance
        
        result = search_web("Hoshiguma")
        if "BeautifulSoup not installed" in result:
             self.skipTest("BeautifulSoup not installed")
             
        self.assertIn("Hoshiguma | Arknights Wiki", result)
        self.assertIn("Hoshiguma is a 6-star Defender.", result)
        self.assertIn("http://example.com/hoshiguma", result)

if __name__ == '__main__':
    unittest.main()
