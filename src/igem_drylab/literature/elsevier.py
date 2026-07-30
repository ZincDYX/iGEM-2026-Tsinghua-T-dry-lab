from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote

import requests


SCOPUS_SEARCH_ENDPOINT = "https://api.elsevier.com/content/search/scopus"
SCIDIR_SEARCH_ENDPOINT = "https://api.elsevier.com/content/search/sciencedirect"
ARTICLE_ENDPOINT = "https://api.elsevier.com/content/article/{id_type}/{identifier}"


def elsevier_headers(api_key: str, inst_token: str | None = None, accept: str = "application/json") -> dict[str, str]:
    headers = {"X-ELS-APIKey": api_key, "Accept": accept}
    if inst_token:
        headers["X-ELS-Insttoken"] = inst_token
    return headers


def search_scopus(api_key: str, query: str, count: int = 25) -> list[dict[str, Any]]:
    response = requests.get(
        SCOPUS_SEARCH_ENDPOINT,
        headers=elsevier_headers(api_key),
        params={"query": query, "count": count},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("search-results", {}).get("entry", []) or []


def fetch_article_xml(api_key: str, *, pii: str | None = None, doi: str | None = None) -> bytes | None:
    if not (pii or doi):
        return None
    identifier, id_type = (pii, "pii") if pii else (doi, "doi")
    url = ARTICLE_ENDPOINT.format(id_type=id_type, identifier=quote(str(identifier), safe=""))
    response = requests.get(url, headers=elsevier_headers(api_key, accept="application/xml"), timeout=60)
    response.raise_for_status()
    return response.content


def extract_text_from_xml(xml_bytes: bytes) -> str:
    root = ET.fromstring(xml_bytes)
    _strip_namespaces(root)
    texts: list[str] = []
    for tag in ("abstract", "section", "para", "p", "simple-para"):
        for element in root.findall(f".//{tag}"):
            text = " ".join("".join(element.itertext()).split())
            if text:
                texts.append(text)
    return "\n".join(texts)


def _strip_namespaces(root: ET.Element) -> None:
    for element in root.iter():
        if isinstance(element.tag, str) and "}" in element.tag:
            element.tag = element.tag.split("}", 1)[1]
