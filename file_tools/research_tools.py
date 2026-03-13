import os
import json
import time
from typing import List, Dict
from file_tools.tools import search_web, fetch_url, add_memory_entry

def _get_genai_client():
    from google import genai
    return genai.Client(
        api_key=os.getenv("GEMINI_API_KEY", "dummy_key"),
        http_options={'base_url': os.getenv("GEMINI_API_BASE_URL", "http://moderator:8000")}
    )

def _generate_sub_queries(client, query, breadths, model_name):
    from google.genai import types
    plan_prompt = f"""
    Research Topic: {query}
    Generate {breadths} specific sub-questions or search queries that would help provide a comprehensive answer to the research topic.
    Return the result as a JSON list of strings.
    """
    response = client.models.generate_content(
        model=model_name,
        contents=plan_prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    sub_queries = json.loads(response.text)
    return sub_queries if isinstance(sub_queries, list) else [query]

def _process_sub_query(client, q, query, visited_urls, findings, model_name):
    search_results = search_web(q)
    if "No results found" in search_results:
        return
    
    import re
    urls = re.findall(r'URL: (https?://\S+)', search_results)
    
    for url in urls[:2]:
        if url in visited_urls:
            continue
        visited_urls.add(url)
        
        print(f"DEEP SEARCH: Fetching {url}")
        content = fetch_url(url, remove_selectors=["header", "footer", "nav", "aside", "script", "style"])
        
        if "Error fetching URL" in content:
            continue
            
        summary_prompt = f"""
        Research Topic: {query}
        Source URL: {url}
        Content: {content[:10000]}
        Extract and summarize relevant information. Be concise.
        """
        sum_res = client.models.generate_content(model=model_name, contents=summary_prompt)
        findings.append({"text": sum_res.text, "source": url, "timestamp": time.time()})

def deep_search(query: str, max_depth: int = 2, breadths: int = 3) -> str:
    """Performs a deep, multi-step research on a given topic."""
    try:
        client = _get_genai_client()
        model_name = "gemini-3-flash-preview"
        findings = []
        visited_urls = set()

        print(f"DEEP SEARCH: Starting research on '{query}'")
        sub_queries = _generate_sub_queries(client, query, breadths, model_name)
        sub_queries.insert(0, query)

        for q in sub_queries[:breadths+1]:
            print(f"DEEP SEARCH: Exploring '{q}'")
            _process_sub_query(client, q, query, visited_urls, findings, model_name)

        print("DEEP SEARCH: Synthesizing findings...")
        all_findings_text = "\n\n".join([f"Source: {f['source']}\n{f['text']}" for f in findings])
        synthesis_prompt = f"Research Topic: {query}\nFindings:\n{all_findings_text}\nProvide a comprehensive report."
        
        final_response = client.models.generate_content(model=model_name, contents=synthesis_prompt)
        report = final_response.text
        
        add_memory_entry(f"Deep Research Report: {query}\n\n{report}", metadata={"type": "research_report", "query": query, "sources": list(visited_urls)}, auto_tag=True)
        return report

    except Exception as e:
        return f"Error during deep search: {e}"
