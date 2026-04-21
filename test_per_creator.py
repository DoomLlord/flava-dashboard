"""
Proverava da li API filtrira transakcije po creator-u.
Pokreni: python test_per_creator.py
"""
from infloww_clientapi import InflowwClient, analyze_transactions

API_KEY = "sk-1940207587098641lcFbaBVjyZJt4ozPXNO3wkhzhAZirmfUVflSTgxTG"
AGENCY_OID = "1940207587098641"

client = InflowwClient(API_KEY, AGENCY_OID)
creators = client.get_creators()

total_net = 0.0
for c in creators:
    cid = str(c.get("id"))
    name = c.get("name")
    txns = client.get_transactions(cid)
    summary = analyze_transactions(txns)
    net = summary["total_net"]
    total_net += net
    print(f"{name:25s}  txns={summary['count']:4d}  net=${net:10,.2f}")

print(f"\n{'TOTAL':25s}  net=${total_net:,.2f}")
