import streamlit as st
from google_auth import get_gspread_client

SHEET_ID = "1YMZgVR3CEmdP83J6Y8jomCCq9idr2khMkSAsBdolJz4"
TAB_NAME = "Reports"

COLUMNS = ["creator", "chatters_headline", "chatters_body", "executive_headline", "executive_body"]


def _get_or_create_tab():
    client = get_gspread_client()
    ss = client.open_by_key(SHEET_ID)
    titles = [ws.title for ws in ss.worksheets()]
    if TAB_NAME not in titles:
        ws = ss.add_worksheet(title=TAB_NAME, rows=100, cols=len(COLUMNS))
        ws.append_row(COLUMNS)
    else:
        ws = ss.worksheet(TAB_NAME)
    return ws


@st.cache_data(ttl=60)
def fetch_all_reports() -> dict:
    """Returns {creator_lower: {chatters: {headline, body}, executive: {headline, body}}}"""
    try:
        client = get_gspread_client()
        ss = client.open_by_key(SHEET_ID)
        titles = [ws.title for ws in ss.worksheets()]
        if TAB_NAME not in titles:
            return {}
        ws = ss.worksheet(TAB_NAME)
        rows = ws.get_all_records()
        result = {}
        for row in rows:
            name = str(row.get("creator", "")).strip().lower()
            if not name:
                continue
            result[name] = {
                "chatters":  {"headline": row.get("chatters_headline", ""),  "body": row.get("chatters_body", "")},
                "executive": {"headline": row.get("executive_headline", ""), "body": row.get("executive_body", "")},
            }
        return result
    except Exception as e:
        print(f"[reports_fetcher] fetch error: {e}")
        return {}


def save_report(creator_key: str, chatters_headline: str, chatters_body: str,
                executive_headline: str, executive_body: str) -> bool:
    try:
        ws = _get_or_create_tab()
        rows = ws.get_all_values()
        headers = rows[0] if rows else COLUMNS

        try:
            col_idx = {h: i + 1 for i, h in enumerate(headers)}
            creator_col = col_idx.get("creator", 1)
        except Exception:
            col_idx = {h: i + 1 for i, h in enumerate(COLUMNS)}
            creator_col = 1

        # Find existing row for this creator
        existing_row = None
        for i, row in enumerate(rows[1:], start=2):
            if row and str(row[0]).strip().lower() == creator_key.lower():
                existing_row = i
                break

        new_values = [
            creator_key.lower(),
            chatters_headline,
            chatters_body,
            executive_headline,
            executive_body,
        ]

        if existing_row:
            ws.update(f"A{existing_row}:E{existing_row}", [new_values])
        else:
            ws.append_row(new_values)

        fetch_all_reports.clear()
        return True
    except Exception as e:
        print(f"[reports_fetcher] save error: {e}")
        return False
