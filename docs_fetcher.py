import os
import difflib
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

DOC_ID = "1pg7zyop3jttIwxrZM2hI0p2Kpqo5qaCNjrpDZoPjHzY"

SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _get_docs_service():
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
    else:
        creds_file = os.path.join(os.path.dirname(__file__), "credentials.json")
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    return build("docs", "v1", credentials=creds)


def _extract_text(content_elements: list) -> list[str]:
    """Izvuci listu paragrafa (stringova) iz Docs content niza."""
    paragraphs = []
    for el in content_elements:
        para = el.get("paragraph")
        if not para:
            continue
        text = "".join(
            r.get("textRun", {}).get("content", "")
            for r in para.get("elements", [])
        ).rstrip("\n")
        paragraphs.append(text)
    return paragraphs


def _parse_reports(paragraphs: list[str]) -> dict:
    result = {
        "chatters":  {"headline": "", "body": "", "found": False},
        "executive": {"headline": "", "body": "", "found": False},
    }

    SECTION_MAP = {
        "chatters report":  "chatters",
        "executive report": "executive",
    }

    current_section = None
    headline_set = False

    for line in paragraphs:
        stripped = line.strip()
        lower = stripped.lower()

        matched = next((k for k in SECTION_MAP if k in lower), None)
        if matched:
            current_section = SECTION_MAP[matched]
            result[current_section]["found"] = True
            headline_set = False
            continue

        if current_section is None or not stripped:
            continue

        sec = result[current_section]
        if not headline_set:
            sec["headline"] = stripped
            headline_set = True
        else:
            sec["body"] = (sec["body"] + "\n" + stripped).lstrip("\n")

    return result


def _collect_tabs(tabs: list, result: dict) -> None:
    """Rekurzivno prolazi kroz sve tabove i child tabove."""
    for tab in tabs:
        title = tab.get("tabProperties", {}).get("title", "").strip()
        content = (
            tab.get("documentTab", {})
               .get("body", {})
               .get("content", [])
        )
        result[title] = _extract_text(content)
        child_tabs = tab.get("childTabs", [])
        if child_tabs:
            _collect_tabs(child_tabs, result)


@st.cache_data(ttl=300)
def fetch_all_reports() -> dict:
    """Učitava sve tabove iz Google Doc-a rekurzivno. Vraća {tab_title: paragraphs_list}."""
    try:
        service = _get_docs_service()
        doc = service.documents().get(
            documentId=DOC_ID,
            includeTabsContent=True,
        ).execute()
        raw_tabs = {}
        _collect_tabs(doc.get("tabs", []), raw_tabs)
        # Parsiramo odmah sve reportove
        result = {}
        for title, paragraphs in raw_tabs.items():
            parsed = _parse_reports(paragraphs)
            parsed["tab_found"] = True
            result[title.strip().lower()] = parsed
        print(f"[docs_fetcher] Loaded {len(result)} tabs: {list(result.keys())}")
        return result
    except Exception as e:
        print(f"[docs_fetcher] Error fetching doc: {e}")
        return {}


def get_creator_reports(base_name: str) -> dict:
    """
    Vraća report za kreatora po base_name (bez FREE/Couple sufiksa).
    """
    empty = {
        "chatters":  {"headline": "", "body": "", "found": False},
        "executive": {"headline": "", "body": "", "found": False},
        "tab_found": False,
    }

    all_reports = fetch_all_reports()
    if not all_reports:
        return empty

    name_lower = base_name.strip().lower()

    # 1. Exact
    if name_lower in all_reports:
        return all_reports[name_lower]

    # 2. Fuzzy
    candidates = difflib.get_close_matches(name_lower, list(all_reports.keys()), n=1, cutoff=0.6)
    if candidates:
        return all_reports[candidates[0]]

    print(f"[docs_fetcher] No tab found for '{base_name}'")
    return empty
