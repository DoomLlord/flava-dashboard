import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def get_gspread_client():
    # If running on Streamlit Cloud, use secrets
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # Local development — use credentials.json file
        creds_file = os.path.join(os.path.dirname(__file__), "credentials.json")
        creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client
