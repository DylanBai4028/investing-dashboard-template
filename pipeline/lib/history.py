"""Reads the manual-asset step-series from data/manual_holdings.yaml.

Infrastructure for any asset with no parseable export at all — you add a dated entry
by hand whenever you check a balance, rather than this module inferring or estimating
anything. Empty by default in this template (every platform here ends up with a real
export), kept live in case a genuinely manual-only asset (e.g. property) comes up.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

MANUAL_HOLDINGS_PATH = Path(__file__).parent.parent.parent / "data" / "manual_holdings.yaml"


def load_manual_holdings(path: Path = MANUAL_HOLDINGS_PATH) -> dict[str, Any]:
    """Load the raw manual_holdings.yaml structure. A file with no actual entries
    (comments only) is valid — yaml.safe_load returns None for that, not {}.
    """
    with open(path) as f:
        return yaml.safe_load(f) or {}


def manual_step_series(raw: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Flatten manual_holdings.yaml into one row per (asset, dated entry).

    Each row: {platform, name, ticker, currency, asset_class, liquid, date, value}.
    For quantity-based assets (crypto), `value` is left as None here — pricing happens
    in prices.py, which needs a current rate, not something this loader should guess at.
    """
    raw = raw if raw is not None else load_manual_holdings()
    rows: list[dict[str, Any]] = []

    for platform, entry in raw.items():
        assets = entry if isinstance(entry, list) else [entry]
        for asset in assets:
            for h in asset["history"]:
                rows.append(
                    {
                        "platform": platform,
                        "name": asset["name"],
                        "ticker": asset.get("ticker"),
                        "currency": asset["currency"],
                        "asset_class": asset["asset_class"],
                        "liquid": asset["liquid"],
                        "date": h["date"] if isinstance(h["date"], date) else h["date"],
                        "value": h.get("value"),
                        "quantity": h.get("quantity"),
                    }
                )
    rows.sort(key=lambda r: (r["platform"], r["name"], r["date"]))
    return rows


def latest_manual_snapshot(raw: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """The most recent dated entry per asset — today's manual-asset snapshot."""
    rows = manual_step_series(raw)
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["platform"], row["name"])
        if key not in latest or row["date"] > latest[key]["date"]:
            latest[key] = row
    return list(latest.values())


def manual_daily_totals(
    date_range: list[date],
    crypto_price_usd: dict[str, float],
    usd_aud_rate: float | None,
    raw: dict[str, Any] | None = None,
) -> pd.Series:
    """Sum of every manual asset's AUD value, forward-filled per asset from its most
    recent recorded entry, over `date_range`. Before an asset's first entry it
    contributes 0 (not tracked yet, not zero balance).
    """
    rows = manual_step_series(raw)
    total = pd.Series(0.0, index=pd.Index(date_range, name="date"))

    by_asset: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        by_asset.setdefault((row["platform"], row["name"]), []).append(row)

    for entries in by_asset.values():
        entries.sort(key=lambda r: r["date"])
        currency = entries[0]["currency"]
        ticker = entries[0].get("ticker")
        series = pd.Series(index=pd.Index(date_range, name="date"), dtype=float)
        for entry in entries:
            if entry["date"] not in series.index:
                continue
            if entry["value"] is not None:
                value_aud = (
                    entry["value"]
                    if currency == "AUD"
                    else (
                        entry["value"] / usd_aud_rate
                        if currency == "USD" and usd_aud_rate
                        else None
                    )
                )
            else:  # quantity-based (crypto) — today's price throughout, see docstring
                price = crypto_price_usd.get(ticker)
                value_aud = (
                    entry["quantity"] * price / usd_aud_rate if price and usd_aud_rate else None
                )
            series.loc[entry["date"]] = value_aud
        series = series.ffill().fillna(0.0)
        total = total.add(series, fill_value=0.0)

    return total


if __name__ == "__main__":
    snapshot = latest_manual_snapshot()
    for row in snapshot:
        label = row["value"] if row["value"] is not None else f"{row['quantity']} {row['ticker']}"
        print(f"{row['platform']:16} {row['name']:32} {row['date']}  {label}")
