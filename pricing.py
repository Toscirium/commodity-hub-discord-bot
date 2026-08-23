"""Price lookups against the same public feed commodity-hub.eu's own
landing pages call client-side (public anon key — not a secret, same one
baked into the site's own HTML). Kept separate from bot.py so it's
testable without a Discord connection.
"""
from __future__ import annotations

import requests

SUPABASE_URL = "https://kcxhsmlqqyarhlmcapmj.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtjeGhzbWxxcXlhcmhsbWNhcG1qIiwi"
    "cm9sZSI6ImFub24iLCJpYXQiOjE3NDU3ODM0MDcsImV4cCI6MjA2MTM1OTQwN30.qC25iAjNhbPVotryl7GONMgYkvg0DzEYp8uxioWzkfs"
)

SYMBOLS: dict[str, dict] = {
    "wti": {"symbol": "CL=F", "label": "WTI Crude"},
    "brent": {"symbol": "BZ=F", "label": "Brent Crude"},
    "natgas": {"symbol": "NG=F", "label": "Natural Gas"},
    "gold": {"symbol": "GC=F", "label": "Gold"},
    "silver": {"symbol": "SI=F", "label": "Silver"},
    "copper": {"symbol": "HG=F", "label": "Copper"},
    "corn": {"symbol": "ZC=F", "label": "Corn"},
    "wheat": {"symbol": "ZW=F", "label": "Wheat"},
}


def fetch_price(commodity: str) -> dict:
    """Returns {label, price, change_pct} or raises KeyError/RuntimeError."""
    if commodity not in SYMBOLS:
        raise KeyError(f"Unknown commodity {commodity!r}. Valid: {', '.join(SYMBOLS)}")
    meta = SYMBOLS[commodity]

    resp = requests.post(
        f"{SUPABASE_URL}/functions/v1/fetch-all-commodities",
        headers={
            "Content-Type": "application/json",
            "apikey": SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        },
        json={"dataDelay": "realtime"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    match = next((c for c in data.get("commodities", []) if c and c.get("symbol") == meta["symbol"]), None)
    if not match:
        raise RuntimeError(f"No live data returned for {commodity}")

    return {
        "label": meta["label"],
        "price": match.get("price"),
        "change_pct": match.get("changePercent", 0.0),
    }
