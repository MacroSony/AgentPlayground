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
        # Use the active model for synthesis, but use flash for sub-steps
        model_name = "gemini-3-flash-preview"
        findings = []
        visited_urls = set()
        current_queries = [query]

        print(f"DEEP SEARCH: Starting research on '{query}' (Depth: {max_depth}, Breadth: {breadths})")

        for depth in range(max_depth):
            print(f"DEEP SEARCH: Depth {depth + 1}/{max_depth}")
            next_queries = []
            
            for q in current_queries:
                print(f"DEEP SEARCH: Exploring query: '{q}'")
                _process_sub_query(client, q, query, visited_urls, findings, model_name)
                
                # After exploring, generate refined sub-queries for the next depth if needed
                if depth < max_depth - 1:
                    new_subs = _generate_sub_queries(client, f"Refine search based on: {q}", breadths, model_name)
                    next_queries.extend(new_subs)
            
            current_queries = list(set(next_queries))[:breadths] # Limit breadths for next level
            if not current_queries:
                break

        print("DEEP SEARCH: Synthesizing findings...")
        # Structuring findings for better synthesis
        findings_summary = ""
        for i, f in enumerate(findings):
            findings_summary += f"--- Finding {i+1} (Source: {f['source']}) ---\n{f['text']}\n\n"

        synthesis_prompt = f"""
        Research Topic: {query}
        
        Collected Findings:
        {findings_summary}
        
        Instructions:
        1. Provide a comprehensive, structured report on the research topic.
        2. Use headers and bullet points for readability.
        3. Cite the sources where appropriate.
        4. Highlight any conflicting information found.
        5. Conclude with a summary of the most important takeaways.
        """
        
        final_response = client.models.generate_content(model=model_name, contents=synthesis_prompt)
        report = final_response.text
        
        add_memory_entry(f"Deep Research Report: {query}\n\n{report}", metadata={"type": "research_report", "query": query, "sources": list(visited_urls)}, auto_tag=True)
        return report

    except Exception as e:
        return f"Error during deep search: {e}"
