import os
import re
import zipfile
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_substack_articles(subdomain: str = "jeremyutley", count: int = 3) -> str:
    """
    Fetches the latest articles from a public Substack and bundles them
    into clean Markdown files inside a ZIP archive for NotebookLM.
    """
    # Clean subdomain if a full URL was provided
    clean_sub = subdomain.replace("https://", "").replace("http://", "").split(".")[0].strip("/")
    base_url = f"https://{clean_sub}.substack.com"
    archive_api = f"{base_url}/api/v1/archive?sort=new&limit={count}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    response = requests.get(archive_api, headers=headers, timeout=15)
    response.raise_for_status()
    posts_data = response.json()

    if not posts_data:
        return f"No published articles found for {clean_sub}."

    created_files = []
    
    for post in posts_data[:count]:
        title = post.get("title", "Untitled")
        subtitle = post.get("subtitle", "")
        post_date = post.get("post_date", "")[:10]  # Format: YYYY-MM-DD
        post_url = post.get("canonical_url", "")

        # Fetch full post page to get clean HTML body
        post_resp = requests.get(post_url, headers=headers, timeout=15)
        soup = BeautifulSoup(post_resp.text, "html.parser")

        # Find the primary post body container
        body_div = soup.find("div", class_="available-content") or soup.find("div", class_="body")
        if not body_div:
            body_div = soup.find("article")

        if not body_div:
            continue

        # Remove boilerplate UI elements (subscribe widgets, buttons, share prompts)
        for element in body_div.find_all(["div", "section"], class_=re.compile(r"subscribe|button|footer|share|social")):
            element.decompose()

        # Build clean Markdown content
        md_lines = [
            f"# {title}",
            f"**Author:** Jeremy Utley  ",
            f"**Published:** {post_date}  ",
            f"**Source:** {post_url}\n",
        ]
        if subtitle:
            md_lines.append(f"> *{subtitle}*\n")

        # Process headings, paragraphs, and blockquotes
        for tag in body_div.find_all(["h1", "h2", "h3", "p", "blockquote", "ul", "ol"]):
            text = tag.get_text(separator=" ", strip=True)
            if not text:
                continue

            # Skip common leftover call-to-actions
            if any(cta in text.lower() for cta in ["subscribe to", "leave a comment", "share this post"]):
                continue

            if tag.name == "h1":
                md_lines.append(f"## {text}\n")
            elif tag.name == "h2":
                md_lines.append(f"### {text}\n")
            elif tag.name == "h3":
                md_lines.append(f"#### {text}\n")
            elif tag.name == "blockquote":
                md_lines.append(f"> {text}\n")
            elif tag.name in ["ul", "ol"]:
                for li in tag.find_all("li"):
                    li_text = li.get_text(strip=True)
                    md_lines.append(f"- {li_text}")
                md_lines.append("")
            else:
                md_lines.append(f"{text}\n")

        # Sanitize filename
        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:45]
        filename = f"{post_date}_{safe_title}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        created_files.append(filename)

    # Package files into a zip
    zip_filename = f"{clean_sub}_latest_{len(created_files)}_articles.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in created_files:
            zipf.write(f)
            os.remove(f)  # Clean up individual markdown files

    return f"Successfully saved {len(created_files)} articles into '{zip_filename}'."

if __name__ == "__main__":
    # Runs automatically when executing: python scraper.py
    result = fetch_substack_articles("jeremyutley", count=3)
    print(result)