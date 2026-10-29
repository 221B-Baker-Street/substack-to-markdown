---
name: substack-to-markdown
description: Fetches published articles from a public Substack publication archive, cleans UI boilerplate, and bundles them into clean Markdown files in a ZIP archive for NotebookLM.
parameters:
  type: object
  properties:
    subdomain:
      type: string
      description: The Substack publication subdomain (e.g., 'jeremyutley').
      default: jeremyutley
    count:
      type: integer
      description: Number of recent articles to scrape.
      default: 3
  required:
    - subdomain
entrypoint: scraper.py:fetch_substack_articles
---

# Substack to Markdown Harvester

This skill queries public Substack archive feeds, strips HTML clutter, and outputs clean Markdown files tailored for NotebookLM podcast and study-guide generation.