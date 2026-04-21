import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

DOC_ID = "1pg7zyop3jttIwxrZM2hI0p2Kpqo5qaCNjrpDZoPjHzY"
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
service = build("docs", "v1", credentials=creds)

doc = service.documents().get(
    documentId=DOC_ID,
    includeTabsContent=True,
).execute()

print("=== TOP LEVEL KEYS ===")
print(list(doc.keys()))

print("\n=== TABS STRUCTURE ===")
tabs = doc.get("tabs", [])
print(f"Number of top-level tabs: {len(tabs)}")

def print_tabs(tabs, indent=0):
    for tab in tabs:
        props = tab.get("tabProperties", {})
        title = props.get("title", "NO TITLE")
        tab_id = props.get("tabId", "")
        children = tab.get("childTabs", [])
        has_content = bool(tab.get("documentTab", {}).get("body", {}).get("content"))
        print(" " * indent + f"- '{title}' (id={tab_id}, hasContent={has_content}, children={len(children)})")
        if children:
            print_tabs(children, indent + 2)

print_tabs(tabs)

print("\n=== RAW FIRST TAB (truncated) ===")
if tabs:
    first = tabs[0]
    print(json.dumps({k: v for k, v in first.items() if k != "documentTab"}, indent=2))
