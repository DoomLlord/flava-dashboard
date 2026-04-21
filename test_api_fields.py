"""
Test skript — ispisuje sirova polja iz Infloww API-ja.
Pokreni: python test_api_fields.py
"""
import json
from infloww_clientapi import InflowwClient

API_KEY = "sk-1940207587098641lcFbaBVjyZJt4ozPXNO3wkhzhAZirmfUVflSTgxTG"
AGENCY_OID = "1940207587098641"

client = InflowwClient(API_KEY, AGENCY_OID)

creators = client.get_creators()
if not creators:
    print("Nema creators")
    exit()

creator = creators[0]
creator_id = str(creator.get("id"))
print(f"\n=== Creator: {creator.get('name')} (ID: {creator_id}) ===")
print("Creator fields:", list(creator.keys()))
print(json.dumps(creator, indent=2))

print("\n\n=== TRANSACTIONS (prva 3) ===")
txns = client.get_transactions(creator_id)
for i, tx in enumerate(txns[:3]):
    print(f"\n--- Transaction {i+1} ---")
    print("Fields:", list(tx.keys()))
    print(json.dumps(tx, indent=2, default=str))

print("\n\n=== REFUNDS (prva 3 ako ih ima) ===")
refunds = client.get_refunds(creator_id)
if refunds:
    for i, ref in enumerate(refunds[:3]):
        print(f"\n--- Refund {i+1} ---")
        print("Fields:", list(ref.keys()))
        print(json.dumps(ref, indent=2, default=str))
else:
    print("Nema refundi.")

print("\n\n=== LINKS (prva 3) ===")
links = client.get_links(creator_id, link_type="TRIAL")
if links:
    for i, link in enumerate(links[:3]):
        print(f"\n--- Link {i+1} ---")
        print("Fields:", list(link.keys()))
        print(json.dumps(link, indent=2, default=str))
else:
    print("Nema TRIAL linkova.")

print("\n\n=== CAMPAIGN LINKS (prva 3) ===")
camp_links = client.get_links(creator_id, link_type="CAMPAIGN")
if camp_links:
    for i, link in enumerate(camp_links[:3]):
        print(f"\n--- Campaign Link {i+1} ---")
        print("Fields:", list(link.keys()))
        print(json.dumps(link, indent=2, default=str))
else:
    print("Nema CAMPAIGN linkova.")

if links:
    print("\n\n=== LINK FANS (za prvi TRIAL link) ===")
    link_id = str(links[0].get("id", ""))
    fans = client.get_link_fans(creator_id, link_id, link_type="TRIAL")
    if fans:
        for i, fan in enumerate(fans[:3]):
            print(f"\n--- Fan {i+1} ---")
            print("Fields:", list(fan.keys()))
            print(json.dumps(fan, indent=2, default=str))
    else:
        print("Nema fanova za ovaj link.")
