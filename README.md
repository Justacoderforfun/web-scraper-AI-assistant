# Web Scraper with Groq AI Integration

This project is a Python-based web scraper that allows you to search DuckDuckGo for queries, scrape the top results, and analyze the extracted content using the Groq API. It provides an interactive experience where you can ask questions about the scraped content, and the AI will respond based on the conversation history.

## Features
- **DuckDuckGo Search**: Searches DuckDuckGo for the given query and returns the top 5 results.
- **Web Scraping**: Extracts up to 10 paragraphs from each page, followed by scraping internal links for further data extraction.
- **AI Analysis with Groq**: Sends the scraped content to the Groq AI API for analysis, remembering the last 10 conversation messages for context.
- **Interactive Q&A**: Allows users to ask questions about the scraped content, with the AI providing answers.

## Requirements
- Python 3.6 or higher
- Required Python libraries:
  - `requests`
  - `beautifulsoup4`
  - `json`
  - `re`
  - `urllib`

You can install the required libraries using `pip`:

```bash
pip install requests beautifulsoup4
