import os
import json
import time
from typing import List, Dict
from file_tools.tools import search_web, fetch_url, add_memory_entry

def deep_search(query: str, max_depth: int = 2, breadths: int = 3) -> str:
    """Performs a deep, multi-step research on a given topic.
    
    Args:
        query: The research topic or question.
        max_depth: How many levels of follow-up questions to explore.
        breadths: How many search results/sub-questions to explore per level.
    """
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY", "dummy_key"),
            http_options={'base_url': os.getenv("GEMINI_API_BASE_URL", "http://moderator:8000")}
        )
        
        # Use Flash for sub-tasks to save budget
        model_name = "gemini-3-flash-preview"
        
        findings = []
        visited_urls = set()
        
        def log_finding(text: str, source: str = None):
            findings.append({"text": text, "source": source, "timestamp": time.time()})

        # Step 1: Initial Search & Plan
        print(f"DEEP SEARCH: Starting research on '{query}'")
        
        plan_prompt = f"""
        Research Topic: {query}
        Generate {breadths} specific sub-questions or search queries that would help provide a comprehensive answer to the research topic.
        Return the result as a JSON list of strings.
        """
        
        response = client.models.generate_content(
            model=model_name,
            contents=plan_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        sub_queries = json.loads(response.text)
        if not isinstance(sub_queries, list):
            sub_queries = [query]
        
        # Add the main query to the list
        sub_queries.insert(0, query)
        
        # Step 2: Iterate through queries
        for q in sub_queries[:breadths+1]:
            print(f"DEEP SEARCH: Exploring '{q}'")
            search_results = search_web(q)
            if "No results found" in search_results:
                continue
                
            # Extract URLs from search results (simple regex)
            import re
            urls = re.findall(r'URL: (https?://\S+)', search_results)
            
            for url in urls[:2]: # Fetch top 2 unique URLs per sub-query
                if url in visited_urls:
                    continue
                visited_urls.add(url)
                
                print(f"DEEP SEARCH: Fetching {url}")
                content = fetch_url(url, remove_selectors=["header", "footer", "nav", "aside", "script", "style"])
                
                if "Error fetching URL" in content:
                    continue
                
                # Summarize the content relative to the main query
                summary_prompt = f"""
                Research Topic: {query}
                Source URL: {url}
                Content: {content[:10000]}
                
                Extract and summarize the most relevant information from this source that helps answer the Research Topic.
                Be concise but thorough.
                """
                
                sum_res = client.models.generate_content(model=model_name, contents=summary_prompt)
                log_finding(sum_res.text, source=url)

        # Step 3: Synthesis
        print("DEEP SEARCH: Synthesizing findings...")
        all_findings_text = "\n\n".join([f"Source: {f['source']}\n{f['text']}" for f in findings])
        
        synthesis_prompt = f"""
        Research Topic: {query}
        Gathered Findings:
        {all_findings_text}
        
        Based on the findings above, provide a comprehensive, well-structured, and detailed report answering the Research Topic.
        Include citations to the sources where appropriate.
        If there are conflicting reports, mention them.
        """
        
        # Use Pro for synthesis if possible, but default to Flash for now to be safe with tool definition
        final_response = client.models.generate_content(model=model_name, contents=synthesis_prompt)
        report = final_response.text
        
        # Save to memory
        add_memory_entry(
            f"Deep Research Report: {query}\n\n{report}",
            metadata={"type": "research_report", "query": query, "sources": list(visited_urls)},
            auto_tag=True
        )
        
        return report

    except Exception as e:
        return f"Error during deep search: {e}"
