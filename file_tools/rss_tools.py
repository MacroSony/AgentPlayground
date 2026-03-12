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
            summary = entry.get('summary', '')
            if summary:
                # Basic HTML strip for summary
                import re
                summary = re.sub('<[^<]+?>', '', summary)
                summary = summary[:200] + "..." if len(summary) > 200 else summary
            
            output.append(f"- {title} ({published})\n  URL: {link}\n  Summary: {summary if summary else 'No summary.'}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error parsing RSS feed: {e}"

def summarize_rss_entry(url: str) -> str:
    """Fetches and summarizes the content of a specific RSS entry URL.
    
    Args:
        url: The URL of the RSS entry to summarize.
    """
    try:
        from file_tools.tools import fetch_url
        content = fetch_url(url)
        if "Error" in content:
            return content
            
        # Using a simple logic here to summarize, or just return first part
        summary = content[:1500] + "..." if len(content) > 1500 else content
        return f"Summary of {url}:\n\n{summary}"
    except Exception as e:
        return f"Error summarizing RSS entry: {e}"
