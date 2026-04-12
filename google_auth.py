import gspread
from google.oauth2.service_account import Credentials
import os

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")


def get_gspread_client():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client
