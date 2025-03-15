import os
import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urlparse, urljoin, parse_qs

# Load API key securely
GROQ_API_KEY = ""  # Replace with environment variable for security
GROQ_MODEL = "llama-3.3-70b-versatile"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Store conversation history
conversation_history = []

def extract_direct_url(duckduckgo_url):
    """Extracts the actual URL from a DuckDuckGo search result link."""
    parsed_url = urlparse(duckduckgo_url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get("uddg", [duckduckgo_url])[0]  # Return original if 'uddg' param is missing

def search_duckduckgo(query):
    """Search DuckDuckGo and return the top 5 results."""
    search_url = f"https://html.duckduckgo.com/html/?q={query}"
    response = requests.get(search_url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for link in soup.find_all("a", class_="result__a", href=True):
        direct_url = extract_direct_url(link["href"])
        if direct_url:
            results.append((link.text, direct_url))
        if len(results) >= 5:
            break

    return results

def get_internal_links(base_url, soup):
    """Extract up to 20 internal links from a page."""
    internal_links = set()
    parsed_base = urlparse(base_url)
    
    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(full_url)

        # Ensure it's an internal link and not a duplicate
        if parsed_url.netloc == parsed_base.netloc and full_url not in internal_links:
            internal_links.add(full_url)
        if len(internal_links) >= 20:
            break

    return list(internal_links)

def scrape_page(url):
    """Scrape a single page and extract content + internal links."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract paragraphs
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        content = "\n".join(paragraphs[:10])  # Limit to first 10 paragraphs

        # Extract additional internal links
        internal_links = get_internal_links(url, soup)

        return content, internal_links
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return None, []

def analyze_with_groq(content, question):
    """Send extracted content and user question to Groq API for analysis with conversation memory."""
    if not GROQ_API_KEY:
        print("❌ Missing Groq API key. Set it in environment variables.")
        return None

    max_length = 4000
    if len(content) > max_length:
        content = content[:max_length] + "...\n[Content Truncated]"

    # Keep only the last 10 messages in memory
    if len(conversation_history) > 10:
        conversation_history.pop(0)

    # Add new question to history
    conversation_history.append({"role": "user", "content": question})

    # Build API request payload with conversation memory
    messages = [{"role": "system", "content": "You are an intelligent assistant answering user questions based on web-scraped content."}]
    messages.append({"role": "user", "content": f"Here is the summarized content:\n\n{content}"})
    messages.extend(conversation_history)

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {"model": GROQ_MODEL, "messages": messages}

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        # Save AI response in memory
        if result.get("choices"):
            ai_response = result["choices"][0]["message"]["content"]
            conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Groq API: {e}")
        return None

def main():
    query = input("🔍 What would you like to search? ").strip()
    results = search_duckduckgo(query)

    if not results:
        print("❌ No search results found.")
        return
    
    print("\n🌍 Top search results:")
    for i, (title, url) in enumerate(results, 1):
        print(f"{i}. {title} ({url})")

    extracted_content = ""
    all_links = set()

    # Scrape each of the 5 search result pages
    for _, url in results:
        content, internal_links = scrape_page(url)
        if content:
            extracted_content += content + "\n\n"
        
        all_links.update(internal_links)  # Store unique internal links

    # Scrape up to 20 additional pages per website
    additional_links = list(all_links)[:100]  # Limit total scraping to avoid excessive requests
    print(f"\n📄 Found {len(additional_links)} internal pages to scrape...")

    for url in additional_links:
        content, _ = scrape_page(url)
        if content:
            extracted_content += content + "\n\n"

    if not extracted_content:
        print("❌ Failed to extract content from the search results.")
        return

    print("\n🧠 AI now remembers the last 10 messages for better conversation!")

    while True:
        question = input("\n❓ Ask a question about the content (or type 'exit' to quit): ").strip()
        if question.lower() == "exit":
            print("👋 Goodbye!")
            break
        
        analysis = analyze_with_groq(extracted_content, question)
        if analysis:
            print("\n🤖 AI Response:")
            print(analysis)

if __name__ == "__main__":
    main()
