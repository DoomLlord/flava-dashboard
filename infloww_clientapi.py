"""
Infloww API Client
===================
Python modul za povlačenje podataka sa Infloww API-ja.
Podržava: Transactions, Refunds, Creators, Links, Link Fans.

Upotreba:
    1. Popuni API_KEY, AGENCY_OID, i CREATOR_ID dole
    2. Pokreni: python infloww_client.py
"""

import requests
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

# ============================================================
# KONFIGURACIJA — POPUNI SVOJE PODATKE OVDE
# ============================================================
API_KEY = "sk-1940207587098641lcFbaBVjyZJt4ozPXNO3wkhzhAZirmfUVflSTgxTG"        # Bearer token iz Infloww-a
AGENCY_OID = "1940207587098641"  # Agency OID iz Infloww-a
CREATOR_ID = "YOUR_CREATOR_ID_HERE"  # Creator ID (nađeš ga kad listaš creators)
# ============================================================

BASE_URL = "https://openapi.infloww.com/v1"


class InflowwClient:
    """Klijent za Infloww API."""

    def __init__(self, api_key: str, agency_oid: str):
        self.api_key = api_key
        self.agency_oid = agency_oid
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Authorization": api_key,
            "x-oid": agency_oid,
        })

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Napravi GET request sa error handling-om."""
        url = f"{BASE_URL}/{endpoint}"
        resp = self.session.get(url, params=params)

        if resp.status_code == 429:
            print("⚠️  Rate limit dostignut. Čekam 10 sekundi...")
            time.sleep(10)
            resp = self.session.get(url, params=params)

        if resp.status_code != 200:
            print(f"❌ Greška {resp.status_code}: {resp.text}")
            # Prikaži x-request-id za support
            req_id = resp.headers.get("x-request-id", "N/A")
            print(f"   x-request-id: {req_id}")
            return {}

        return resp.json()

    def _paginate(self, endpoint: str, params: dict, max_pages: int = 50) -> tuple[list, bool]:
        """
        Automatska paginacija.
        Vraća (items, hit_limit) — hit_limit=True SAMO kad je dostignut max broj stranica,
        što ukazuje da API možda ne filtrira po creatorId ispravno.
        """
        all_items = []
        page = 0

        while page < max_pages:
            result = self._get(endpoint, params)
            if not result or "data" not in result:
                break  # API greška — nije limit, samo prekidamo

            items = result.get("data", {}).get("list", [])
            all_items.extend(items)

            has_more = result.get("hasMore", False)
            cursor = result.get("cursor")

            if not has_more or not cursor:
                return all_items, False  # Prirodan kraj paginacije

            params["cursor"] = cursor
            page += 1
            time.sleep(0.25)

        # hit_limit=True samo ako smo zaista prošli sve stranice
        hit_limit = page >= max_pages
        return all_items, hit_limit

    # ----------------------------------------------------------
    # ENDPOINTS
    # ----------------------------------------------------------

    def get_creators(self, limit: int = 100) -> list:
        """Vrati listu svih connected creators."""
        params = {"platformCode": "OnlyFans", "limit": limit}
        items, _ = self._paginate("creators", params)
        return items

    def get_transactions(
        self,
        creator_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> tuple[list, bool]:
        """Vrati (transakcije, hit_limit) za creatora."""
        if not start_time:
            start_time = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {
            "platformCode": "OnlyFans",
            "creatorId": creator_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }
        return self._paginate("transactions", params)

    def get_refunds(
        self,
        creator_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> tuple[list, bool]:
        """Vrati (refunde, hit_limit) za creatora."""
        if not start_time:
            start_time = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {
            "platformCode": "OnlyFans",
            "creatorId": creator_id,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }
        return self._paginate("refunds", params)

    def get_links(
        self,
        creator_id: str,
        link_type: str = "CAMPAIGN",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        if not start_time:
            start_time = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        if not end_time:
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {
            "platformCode": "OnlyFans",
            "creatorId": creator_id,
            "linkType": link_type,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }
        items, _ = self._paginate("links", params)
        return items

    def get_link_fans(
        self,
        creator_id: str,
        link_id: str,
        link_type: str = "TRIAL",
        limit: int = 100,
    ) -> list:
        """Vrati fanove za specifičan link."""
        params = {
            "platformCode": "OnlyFans",
            "creatorId": creator_id,
            "linkId": link_id,
            "linkType": link_type,
            "limit": limit,
        }
        items, _ = self._paginate("linkfans", params)
        return items


# ==============================================================
# HELPER FUNKCIJE ZA ANALIZU
# ==============================================================

def parse_amount(value) -> float:
    """
    Parsira amount iz API-ja.
    API vraća amounts u centima kao string (npr. '7400' = $74.00).
    """
    try:
        return float(value) / 100
    except (TypeError, ValueError):
        return 0.0


def format_usd(amount: float) -> str:
    """Formatira broj kao USD."""
    return f"${amount:,.2f}"


def timestamp_to_date(ts) -> str:
    """Konvertuje unix timestamp (ms) u čitljiv datum."""
    try:
        ts_int = int(ts)
        return datetime.fromtimestamp(ts_int / 1000, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        )
    except (TypeError, ValueError):
        return str(ts)


def analyze_transactions(transactions: list) -> dict:
    """Analiziraj transakcije i vrati summary."""
    summary = {
        "total_gross": 0.0,
        "total_fee": 0.0,
        "total_net": 0.0,
        "count": len(transactions),
        "by_type": {},
        "by_date": {},
    }

    for tx in transactions:
        gross = parse_amount(tx.get("amount", 0))
        fee = parse_amount(tx.get("fee", 0))
        net = parse_amount(tx.get("net", 0))
        tx_type = tx.get("type", "Unknown")
        date_str = timestamp_to_date(tx.get("createdTime", ""))[:10]  # samo datum

        summary["total_gross"] += gross
        summary["total_fee"] += fee
        summary["total_net"] += net

        # Po tipu transakcije
        if tx_type not in summary["by_type"]:
            summary["by_type"][tx_type] = {"gross": 0.0, "net": 0.0, "count": 0}
        summary["by_type"][tx_type]["gross"] += gross
        summary["by_type"][tx_type]["net"] += net
        summary["by_type"][tx_type]["count"] += 1

        # Po datumu
        if date_str not in summary["by_date"]:
            summary["by_date"][date_str] = {"gross": 0.0, "net": 0.0, "count": 0}
        summary["by_date"][date_str]["gross"] += gross
        summary["by_date"][date_str]["net"] += net
        summary["by_date"][date_str]["count"] += 1

    return summary


def analyze_refunds(refunds: list) -> dict:
    """Analiziraj refunde."""
    summary = {
        "total_amount": 0.0,
        "count": len(refunds),
        "by_type": {},
    }

    for ref in refunds:
        amount = parse_amount(ref.get("paymentAmount", 0))
        tx_type = ref.get("transactionType", "Unknown")

        summary["total_amount"] += amount

        if tx_type not in summary["by_type"]:
            summary["by_type"][tx_type] = {"amount": 0.0, "count": 0}
        summary["by_type"][tx_type]["amount"] += amount
        summary["by_type"][tx_type]["count"] += 1

    return summary


def print_report(creators, transactions_summary, refunds_summary):
    """Štampaj izveštaj u terminal."""
    print("\n" + "=" * 60)
    print("  INFLOWW PERFORMANCE REPORT")
    print("=" * 60)

    # Creators
    print(f"\n📋 Connected Creators: {len(creators)}")
    for c in creators:
        print(f"   • {c.get('name', 'N/A')} (@{c.get('userName', 'N/A')}) — ID: {c.get('id')}")

    # Transactions
    ts = transactions_summary
    print(f"\n💰 Transactions (Last 30 Days)")
    print(f"   Total Transactions: {ts['count']}")
    print(f"   Gross:  {format_usd(ts['total_gross'])}")
    print(f"   Fees:   {format_usd(ts['total_fee'])}")
    print(f"   Net:    {format_usd(ts['total_net'])}")

    if ts["by_type"]:
        print(f"\n   Breakdown by Type:")
        for t, data in sorted(ts["by_type"].items(), key=lambda x: x[1]["net"], reverse=True):
            print(f"     {t:20s}  {format_usd(data['net']):>12s} net  ({data['count']} txns)")

    if ts["by_date"]:
        print(f"\n   Daily Breakdown (last 10 days):")
        sorted_dates = sorted(ts["by_date"].items(), reverse=True)[:10]
        for date, data in sorted_dates:
            print(f"     {date}  {format_usd(data['net']):>12s} net  ({data['count']} txns)")

    # Refunds
    rs = refunds_summary
    print(f"\n🔄 Refunds (Last 30 Days)")
    print(f"   Total Refunds: {rs['count']}")
    print(f"   Total Amount:  {format_usd(rs['total_amount'])}")
    if rs["by_type"]:
        for t, data in rs["by_type"].items():
            print(f"     {t:20s}  {format_usd(data['amount']):>12s}  ({data['count']} refunds)")

    # Chargeback rate
    if ts["total_gross"] > 0:
        chargeback_rate = (rs["total_amount"] / ts["total_gross"]) * 100
        print(f"\n   📊 Chargeback Rate: {chargeback_rate:.2f}%")

    print("\n" + "=" * 60)


# ==============================================================
# MAIN
# ==============================================================

def main():
    # Provera konfiguracije
    if "YOUR_" in API_KEY or "YOUR_" in AGENCY_OID:
        print("❌ Popuni API_KEY i AGENCY_OID na vrhu fajla!")
        print("   Generiši ih u Infloww → Settings → API Key Management")
        return

    print("🔄 Povezivanje na Infloww API...")
    client = InflowwClient(API_KEY, AGENCY_OID)

    # 1. Lista creators
    print("📋 Učitavam creators...")
    creators = client.get_creators()
    if not creators:
        print("❌ Nema creators ili greška u autentifikaciji.")
        print("   Proveri API_KEY i AGENCY_OID.")
        return

    print(f"   ✅ Nađeno {len(creators)} creators")

    # Ako CREATOR_ID nije setovan, uzmi prvog
    creator_id = CREATOR_ID
    if "YOUR_" in creator_id:
        creator_id = creators[0].get("id")
        print(f"   ℹ️  Koristim prvog creatora: {creators[0].get('name')} (ID: {creator_id})")

    # 2. Transakcije (30 dana)
    print("💰 Učitavam transakcije...")
    transactions, hit_limit = client.get_transactions(creator_id)
    print(f"   ✅ Nađeno {len(transactions)} transakcija" + (" ⚠️ udarilo limit!" if hit_limit else ""))

    # 3. Refundi (30 dana)
    print("🔄 Učitavam refunde...")
    refunds, _ = client.get_refunds(creator_id)
    print(f"   ✅ Nađeno {len(refunds)} refunda")

    # Analiza
    tx_summary = analyze_transactions(transactions)
    ref_summary = analyze_refunds(refunds)

    # Izveštaj
    print_report(creators, tx_summary, ref_summary)


if __name__ == "__main__":
    main()
