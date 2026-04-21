import streamlit as st
from datetime import datetime, timedelta, timezone
from infloww_clientapi import InflowwClient, analyze_transactions, analyze_refunds

_API_KEY = "sk-1940207587098641lcFbaBVjyZJt4ozPXNO3wkhzhAZirmfUVflSTgxTG"
_AGENCY_OID = "1940207587098641"


def week_range(offset: int = 0) -> tuple[str, str]:
    """
    Vraća (start, end) za nedelju.
    offset=0 → tekuća nedelja (pon 00:00 – sada)
    offset=1 → prošla nedelja (pon 00:00 – ned 23:59:59)
    offset=2 → pre dve nedelje, itd.
    """
    now = datetime.now(timezone.utc)
    this_monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_start = this_monday - timedelta(weeks=offset)
    week_end = now if offset == 0 else week_start + timedelta(weeks=1) - timedelta(seconds=1)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return week_start.strftime(fmt), week_end.strftime(fmt)


def current_week_range() -> tuple[str, str]:
    return week_range(0)


@st.cache_data(ttl=300)
def get_infloww_creators() -> list:
    client = InflowwClient(_API_KEY, _AGENCY_OID)
    return client.get_creators()


@st.cache_data(ttl=300)
def get_creator_stats(creator_id: str, week_offset: int = 0) -> tuple:
    """
    Vraća (tx_summary, ref_summary, raw_txns, trial_links, campaign_links, data_warning).
    week_offset=0 → tekuća nedelja, 1 → prošla, itd.
    """
    client = InflowwClient(_API_KEY, _AGENCY_OID)
    ws, we = week_range(week_offset)

    txns, txn_hit_limit = client.get_transactions(creator_id, start_time=ws, end_time=we)
    refunds, _ = client.get_refunds(creator_id, start_time=ws, end_time=we)
    trial_links = client.get_links(creator_id, link_type="TRIAL")
    campaign_links = client.get_links(creator_id, link_type="CAMPAIGN")

    data_warning = None
    if txn_hit_limit:
        data_warning = (
            "⚠️ Podaci za ovog creatora možda nisu tačni — API je vratio maksimalan broj transakcija "
            "(5000), što ukazuje da filter po creator ID možda ne radi ispravno. "
            "Prikazani brojevi mogu biti zbirni podaci za celu agenciju."
        )

    return (
        analyze_transactions(txns),
        analyze_refunds(refunds),
        txns,
        trial_links,
        campaign_links,
        data_warning,
    )
