import feedparser
import httpx

def parse_rss_feed(url: str) -> str:
    """Parses an RSS feed and returns the titles and links of the latest entries.

    Args:
        url: The URL of the RSS feed.
    """
    try:
        # Use httpx to fetch the feed content for better control
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            feed_content = response.text
            
        feed = feedparser.parse(feed_content)
        
        if not feed.entries:
            return f"No entries found in feed: {url}"
            
        output = [f"Latest entries from {feed.feed.get('title', url)}:"]
        for entry in feed.entries[:5]:
            title = entry.get('title', 'No Title')
            link = entry.get('link', 'No Link')
            published = entry.get('published', 'No Date')
            output.append(f"- {title} ({published})\n  URL: {link}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error parsing RSS feed: {e}"
