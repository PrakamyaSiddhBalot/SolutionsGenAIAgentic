import os
import requests
import trafilatura
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.environ["SERPER_API_KEY"]

MAX_CHARS = 8000


def web_search(
    query: str,
    num_results: int = 5
) -> dict:
    """
    Search the web using Serper.

    Returns:
    {
        "results": [
            {
                "title": "...",
                "link": "...",
                "snippet": "..."
            }
        ]
    }
    """

    try:

        response = requests.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "q": query,
                "num": num_results
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        results = []

        for item in data.get("organic", []):

            results.append(
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                }
            )

        return {"results": results}

    except Exception as e:

        return {
            "error": str(e)
        }


def web_fetch(url: str) -> dict:
    """
    Fetch and extract readable text from a webpage.

    Returns:
    {
        "content": "...page text..."
    }
    """

    try:

        headers = {
            "User-Agent":
            "Mozilla/5.0 (compatible; ResearchDesk/1.0)"
        }

        response = requests.get(
            url,
            headers=headers,
            allow_redirects=True,
            timeout=10
        )

        response.raise_for_status()

        html = response.text

        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True
        )

        if text is None:

            return {
                "error": "Could not extract page content."
            }

        if len(text) > MAX_CHARS:

            text = (
                text[:MAX_CHARS]
                + "\n\n[...truncated]"
            )

        return {
            "content": text
        }

    except Exception as e:

        return {
            "error": str(e)
        }
