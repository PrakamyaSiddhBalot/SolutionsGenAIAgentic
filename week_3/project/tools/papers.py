"""
Paper search and read tools using the Hugging Face Papers API.

Provides:

    paper_search(query, limit=5)
    read_paper(arxiv_id)

Returns structured dictionaries suitable for tool calling.
"""

import time
import requests
import certifi

HF_BASE_URL = "https://huggingface.co"


def _get(url, params=None, retries=5):
    """
    Robust GET request with retries.
    """

    last_error = None

    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=30,
                verify=certifi.where(),
            )

            response.raise_for_status()

            return response

        except Exception as e:
            last_error = e

            print(
                f"Attempt {attempt + 1} failed: {e}"
            )

            time.sleep(1)

    raise last_error


def paper_search(
    query: str,
    limit: int = 5,
) -> dict:
    """
    Search papers.

    Returns:
    {
        "papers": [
            {
                "arxiv_id": "...",
                "title": "...",
                "abstract": "...",
                "url": "..."
            }
        ]
    }
    """

    response = _get(
        f"{HF_BASE_URL}/api/papers/search",
        params={"q": query},
    )

    papers = response.json()

    results = []

    for item in papers[:limit]:

        paper = item["paper"]

        arxiv_id = paper["id"]

        results.append(
            {
                "arxiv_id": arxiv_id,
                "title": paper.get("title", ""),
                "abstract": paper.get(
                    "summary",
                    ""
                ),
                "url": (
                    f"https://arxiv.org/abs/"
                    f"{arxiv_id}"
                ),
            }
        )

    return {
        "papers": results
    }


def read_paper(
    arxiv_id: str,
) -> dict:
    """
    Read a paper.

    Returns:
    {
        "title": "...",
        "abstract": "...",
        "content": "...",
        "url": "..."
    }
    """

    metadata_response = _get(
        f"{HF_BASE_URL}/api/papers/{arxiv_id}"
    )

    metadata = metadata_response.json()

    title = metadata.get(
        "title",
        ""
    )

    abstract = metadata.get(
        "summary",
        ""
    )

    markdown_content = ""

    try:
        md_response = _get(
            f"{HF_BASE_URL}/api/papers/{arxiv_id}.md"
        )

        markdown_content = md_response.text

    except Exception:
        markdown_content = abstract

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "abstract": abstract,
        "content": markdown_content,
        "url": (
            f"https://arxiv.org/abs/"
            f"{arxiv_id}"
        ),
    }


if __name__ == "__main__":

    print("\nSEARCH TEST\n")

    results = paper_search(
        "attention"
    )

    print(results)

    print("\nREAD TEST\n")

    paper = read_paper(
        "1706.03762"
    )

    print(
        paper["title"]
    )

    print()

    print(
        paper["abstract"][:500]
    )
