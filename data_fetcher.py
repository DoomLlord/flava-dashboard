import pandas as pd
import streamlit as st
import traceback
from google_auth import get_gspread_client

SHEET_ID = "1YMZgVR3CEmdP83J6Y8jomCCq9idr2khMkSAsBdolJz4"

COLUMNS = [
    "Fan Name",
    "Username",
    "Custom price",
    "Paid",
    "AMOUNT",
    "Date",
    "Delivered By Cuhvet",
    "Received",
    "Notes",
]


def parse_amount(value):
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = str(value).replace("$", "").strip()
    if "," in cleaned and "." in cleaned:
        comma_pos = cleaned.rfind(",")
        dot_pos = cleaned.rfind(".")
        if comma_pos > dot_pos:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_sheet(ws) -> pd.DataFrame:
    all_values = ws.get_all_values()
    if len(all_values) < 2:
        return pd.DataFrame(columns=COLUMNS)
    headers = [h.strip() for h in all_values[0]]
    data = all_values[1:]
    df = pd.DataFrame(data, columns=headers)
    if "Fan Name" not in df.columns:
        return pd.DataFrame(columns=COLUMNS)
    df = df[df["Fan Name"].str.strip() != ""]
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[COLUMNS].copy()
    df["AMOUNT"] = df["AMOUNT"].apply(parse_amount)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


@st.cache_data(ttl=300)
def get_sheet_names() -> list[str]:
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SHEET_ID)
        return [ws.title for ws in spreadsheet.worksheets()]
    except Exception as e:
        print(traceback.format_exc())
        st.error(f"Error loading sheet names: {e}")
        return []


@st.cache_data(ttl=300)
def fetch_sheet_data(sheet_name: str) -> pd.DataFrame:
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(SHEET_ID)
        ws = spreadsheet.worksheet(sheet_name)
        return _parse_sheet(ws)
    except Exception as e:
        print(traceback.format_exc())
        st.error(f"Error fetching sheet '{sheet_name}': {e}")
        return pd.DataFrame(columns=COLUMNS)
