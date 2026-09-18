"""Combines the transaction-based reconstruction (backfill.py) with the manual-asset
step-series (history.py) into the snapshot + time-series data the dashboard needs.

Design note (an honest gap, not silently papered over): "total contributed" is
computed from real data for stock/crypto platforms (buys) and any ledger platform with
its own contribution rows — but a platform tracked only as a manual point-in-time
balance has no contribution *transactions* on record, so its contribution figure is
reported as None/"not tracked" rather than approximated from the current balance,
which would wrongly count investment returns as contributions.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from config import ILLIQUID_PLATFORMS, classify_asset_class
from prices import get_fx_series, get_sector


def stock_holdings_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    """Per (platform, ticker): currency, current quantity, average cost basis (rough,
    not tax-lot-accurate), and realized gain/loss from sells so far.

    Grouped by (platform, ticker), not ticker alone — the same ticker can be held on
    more than one platform as genuinely separate positions.
    """
    rows = []
    for (platform, ticker), tx in transactions.groupby(["platform", "ticker"]):
        currency = tx["currency"].iloc[0]
        buys = tx[tx["type"] == "buy"]
        sells = tx[tx["type"] == "sell"]
        divs = tx[tx["type"] == "dividend"]

        bought_qty = buys["quantity"].sum()
        bought_cost = (buys["quantity"] * buys["price"]).sum()
        avg_cost = bought_cost / bought_qty if bought_qty else 0.0

        sold_qty = sells["quantity"].sum()
        realized = (
            ((sells["price"] - avg_cost) * sells["quantity"]).sum() if not sells.empty else 0.0
        )

        current_qty = bought_qty - sold_qty
        current_cost_basis = current_qty * avg_cost
        dividends_received = divs["quantity"].sum()  # dividend rows store cash amount here

        rows.append(
            {
                "ticker": ticker,
                "platform": platform,
                "currency": currency,
                "quantity": current_qty,
                "cost_basis": current_cost_basis,
                "realized_gain": realized,
                "dividends_received": dividends_received,
                "asset_class": classify_asset_class(ticker),
            }
        )
    return pd.DataFrame(rows)


def value_holdings_today(holdings: pd.DataFrame, daily_reconstructed: pd.DataFrame) -> pd.DataFrame:
    """Attach today's market value, day change, and sector to each stock holding —
    read from `daily_reconstructed` (backfill.reconstruct_net_worth's output), not
    re-fetched independently, so the day-change figure and the reconstructed history
    always describe the same underlying numbers.
    """
    out = holdings.copy()
    values, sectors, day_changes = [], [], []
    for _, row in out.iterrows():
        series = daily_reconstructed[
            (daily_reconstructed["ticker"] == row["ticker"])
            & (daily_reconstructed["platform"] == row["platform"])
        ].sort_values("date")
        if series.empty:
            values.append(None)
            day_changes.append(None)
        else:
            values.append(series["value_aud"].iloc[-1])
            day_changes.append(
                series["value_aud"].iloc[-1] - series["value_aud"].iloc[-2]
                if len(series) >= 2
                else 0.0
            )
        sectors.append(get_sector(row["ticker"]))
    out["value_aud"] = values
    out["sector"] = sectors
    out["day_change_aud"] = day_changes
    return out


def value_manual_holdings(manual_snapshot: list[dict]) -> pd.DataFrame:
    """Attach today's value (AUD) to each manual-asset snapshot row — a lump balance
    converted at today's FX rate. Only value-based entries are supported; this
    function is only ever called with whatever's left in data/manual_holdings.yaml
    once every platform with a real export has graduated out of it.
    """
    rows = []
    for asset in manual_snapshot:
        value_native = asset["value"]
        if asset["currency"] == "AUD":
            value_aud = value_native
        else:
            fx = get_fx_series(asset["currency"], date.today() - timedelta(days=7))
            rate = fx["rate"].iloc[-1] if not fx.empty else None
            value_aud = value_native / rate if rate else None
        rows.append({**asset, "value_aud": value_aud, "contributed_aud": None})
    return pd.DataFrame(rows)


def monthly_dividends(transactions: pd.DataFrame, months: int = 12) -> list[float]:
    """Dividend cash received per month, oldest to newest, trailing `months` months."""
    divs = transactions[transactions["type"] == "dividend"].copy()
    month_starts = pd.date_range(
        end=pd.Timestamp(date.today()).to_period("M").to_timestamp(), periods=months, freq="MS"
    )
    if divs.empty:
        return [0.0] * months
    divs["month"] = pd.to_datetime(divs["date"]).dt.to_period("M").dt.to_timestamp()
    by_month = divs.groupby("month")["quantity"].sum()  # dividend rows store cash in `quantity`
    return [float(by_month.get(m, 0.0)) for m in month_starts]


def build_snapshot(
    transactions: pd.DataFrame,
    manual_snapshot: list[dict],
    daily_reconstructed: pd.DataFrame,
    ledger_holdings: list[dict] | None = None,
) -> dict:
    """Today's full snapshot: per-holding detail plus every rollup the dashboard needs
    (platform, asset-class, sector, currency, liquid/illiquid, broker split).
    `daily_reconstructed` is backfill.reconstruct_net_worth's output — the single
    source of truth for current stock values and day change. `ledger_holdings` is for
    platforms with a real daily-balance ledger instead of a transaction/ticker history
    — pre-built dicts in the same shape as stocks_records, computed by the caller
    (run_dashboard.py) from that platform's own parser.
    """
    stocks = value_holdings_today(stock_holdings_summary(transactions), daily_reconstructed)
    manual = value_manual_holdings(manual_snapshot)

    stocks_records = stocks.assign(liquid=True, contributed_aud=stocks["cost_basis"]).to_dict(
        "records"
    )
    manual_records = manual.assign(
        cost_basis=None, realized_gain=0.0, dividends_received=0.0, day_change_aud=0.0
    ).to_dict("records")
    ledger_records = ledger_holdings or []
    all_holdings = stocks_records + manual_records + ledger_records

    total_nw = sum(h["value_aud"] or 0 for h in all_holdings)
    liquid_nw = sum(
        h["value_aud"] or 0
        for h in all_holdings
        if h.get("liquid", True) and h["platform"] not in ILLIQUID_PLATFORMS
    )
    total_contributed = sum(
        h.get("contributed_aud") or 0 for h in stocks_records + ledger_records
    )  # manual-only platforms: still not tracked, no contribution data exists for them
    total_unrealized = sum(
        (h["value_aud"] - h["cost_basis"])
        for h in stocks_records + ledger_records
        if h["value_aud"] is not None and h.get("cost_basis") is not None
    )
    total_realized = sum(h.get("realized_gain") or 0 for h in all_holdings)
    total_day_change = sum(h.get("day_change_aud") or 0 for h in all_holdings)

    def rollup(key: str) -> dict[str, float]:
        out: dict[str, float] = {}
        for h in all_holdings:
            k = h.get(key) or "Unclassified"
            out[k] = out.get(k, 0.0) + (h["value_aud"] or 0)
        return out

    broker_only = [h for h in stocks_records if h["platform"] in ("Meridian", "Northbridge")]
    broker_split = {
        "Meridian": sum(h["value_aud"] or 0 for h in broker_only if h["platform"] == "Meridian"),
        "Northbridge": sum(
            h["value_aud"] or 0 for h in broker_only if h["platform"] == "Northbridge"
        ),
    }

    realized_by_platform: dict[str, float] = {}
    for h in stocks_records:
        realized_by_platform[h["platform"]] = realized_by_platform.get(h["platform"], 0.0) + (
            h.get("realized_gain") or 0
        )
    for h in manual_records + ledger_records:
        realized_by_platform.setdefault(h["platform"], 0.0)

    return {
        "realized_by_platform": realized_by_platform,
        "monthly_dividends": monthly_dividends(transactions),
        "holdings": all_holdings,
        "total_net_worth": total_nw,
        "liquid_net_worth": liquid_nw,
        "total_contributed": total_contributed,
        "total_unrealized": total_unrealized,
        "total_realized": total_realized,
        "total_day_change": total_day_change,
        "by_platform": rollup("platform"),
        "by_asset_class": rollup("asset_class"),
        "by_currency": rollup("currency"),
        # "equities only" — crypto has a sector label ("Crypto", see config.py) so it
        # can be excluded here cleanly, but it isn't a GICS sector and shouldn't appear
        # in a chart titled "sector allocation"
        "by_sector": {
            h["ticker"]: h["sector"]
            for h in stocks_records
            if h.get("sector") and h["sector"] != "Crypto"
        },
        "sector_totals": {
            s: sum(
                h["value_aud"] or 0
                for h in stocks_records
                if h.get("sector") == s and s != "Crypto"
            )
            for s in {h.get("sector") for h in stocks_records if h.get("sector")}
            if s != "Crypto"
        },
        "broker_split": broker_split,
    }


if __name__ == "__main__":
    from backfill import reconstruct_net_worth
    from history import latest_manual_snapshot
    from schema import sample_transactions

    tx = sample_transactions()
    manual = latest_manual_snapshot()  # empty until a manual asset is entered
    daily = reconstruct_net_worth(tx)
    snapshot = build_snapshot(tx, manual, daily)

    print(f"Total net worth:     ${snapshot['total_net_worth']:,.2f}")
    print(f"Liquid net worth:    ${snapshot['liquid_net_worth']:,.2f}")
    print(f"Total contributed:   ${snapshot['total_contributed']:,.2f} (stocks only, manual n/a)")
    print(f"Unrealized gain:     ${snapshot['total_unrealized']:,.2f}")
    print(f"Realized gain:       ${snapshot['total_realized']:,.2f}")
    print(f"Day change:          ${snapshot['total_day_change']:,.2f}")
    print(f"\nBy platform:   {snapshot['by_platform']}")
    print(f"By asset class: {snapshot['by_asset_class']}")
    print(f"By currency:    {snapshot['by_currency']}")
    print(f"Sector totals:  {snapshot['sector_totals']}")
    print(f"Broker split:   {snapshot['broker_split']}")
