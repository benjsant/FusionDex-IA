"""MediaWiki helpers shared by IF-wiki extract scripts."""

from __future__ import annotations

import re

from etl.utils.http import get_json

WIKI_API = "https://infinitefusion.fandom.com/api.php"

_WIKILINK_RE  = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
_BOLD_RE      = re.compile(r"'''?([^']+)'''?")
_HTML_TAG_RE  = re.compile(r"<[^>]+>")
_TEMPLATE_RE  = re.compile(r"\{\{[^}]+\}\}")


def fetch_wikitext(page: str) -> str:
    """Fetch raw wikitext of a page via the MediaWiki `parse` API.

    Raises RuntimeError if the API call fails or returns an unexpected shape.
    """
    data = get_json(WIKI_API, params={
        "action": "parse",
        "page":   page,
        "prop":   "wikitext",
        "format": "json",
    })
    if not data or "parse" not in data:
        raise RuntimeError(f"Failed to fetch wiki page: {page}")
    return data["parse"]["wikitext"]["*"]


def clean_wikitext(text: str, *, strip_html: bool = True, strip_templates: bool = False) -> str:
    """Strip common wiki markup. Returns trimmed plain text.

    Always strips:
        - `[[target|display]]` → `display`, `[[target]]` → `target`
        - `'''bold'''` / `''italic''` markers

    Optional (on by default where relevant):
        - `strip_html`      — remove `<tag>` HTML sequences
        - `strip_templates` — remove `{{...}}` template invocations
    """
    text = _WIKILINK_RE.sub(r"\1", text)
    text = _BOLD_RE.sub(r"\1", text)
    if strip_html:
        text = _HTML_TAG_RE.sub("", text)
    if strip_templates:
        text = _TEMPLATE_RE.sub("", text)
    return text.strip()
