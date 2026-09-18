"""Parses SouthernCross's member-transaction CSVs into a real daily AUD balance
series and a contributions series.

SouthernCross is a template stand-in for a typical AU superannuation fund. Built
against `data/exports/SouthernCross.MemberTransactions.*.csv`: one file per financial
year, mirroring Meridian's per-FY export pattern. Unlike Kowhai's ledger, there's
**no running balance column** — only a per-transaction `Total Amount` — so the balance
has to be reconstructed as a cumulative sum, not read directly.

Two real-world quirks this parser accounts for explicitly:
  - "Investments - Member Direct transfer" rows show money leaving one investment
    option with no offsetting positive amount in the same row — these are internal
    switches into the fund's own self-managed option, not money leaving the fund, and
    are excluded from the balance reconstruction entirely (see DIRECT_TRANSFER_TITLE
    below), since counting them would understate the real balance.
  - "Total contributed" is CONTRIBUTIONS (gross employer/SG amounts) plus the
    contributions-tax rows ("Tax - Contributions", "Tax - Transfer in") — the *net*
    amount that actually landed in the account from external sources, not the gross
    pre-tax figure, and not netted against ongoing fees either (a cost of holding the
    investment, not part of what was contributed).

No FX conversion needed — this platform is natively AUD.
"""

from __future__ import annotations

import glob
from datetime import date
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"

# Internal reallocations within the fund (into its own self-managed option), not a
# real outflow. Excluded from the balance reconstruction.
DIRECT_TRANSFER_TITLE = "Investments - Member Direct transfer"

CONTRIBUTION_TAX_TITLES = {"Tax - Contributions", "Tax - Transfer in"}

# Both the fee charges ("Fee - ...") and their partial tax-deductibility rebate
# ("Tax benefit - ..." — the fund claims the tax deduction on fees within the fund and
# passes part of it back) share this Category — net of both is the real out-of-pocket
# cost, not just the gross fee.
FEE_CATEGORY = "FEES"


def _read_raw() -> pd.DataFrame:
    files = sorted(glob.glob(str(EXPORTS_DIR / "SouthernCross.MemberTransactions.*.csv")))
    if not files:
        raise FileNotFoundError(f"No SouthernCross export found in {EXPORTS_DIR}")
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    # per-FY exports could in principle overlap at the boundary — dedupe defensively,
    # same pattern as parse_meridian.py's multi-file merge
    df = df.drop_duplicates(subset=["Date", "Category", "Title", "Total Amount"])
    return df.sort_values("Date")


def parse_daily_balance() -> pd.DataFrame:
    """[date, balance_aud] — cumulative sum of every transaction's Total Amount,
    excluding the internal Direct transfer rows (see module docstring). One row per
    date that had a real transaction; the dashboard's own forward-fill covers the
    gaps between them.
    """
    raw = _read_raw()
    real = raw[raw["Title"] != DIRECT_TRANSFER_TITLE]
    daily_delta = real.groupby("Date")["Total Amount"].sum()
    cumulative = daily_delta.cumsum()
    return pd.DataFrame({"date": cumulative.index, "balance_aud": cumulative.values})


def parse_contributions() -> pd.DataFrame:
    """[date, amount_aud] — net contribution amounts that actually landed in the
    account (gross contributions minus the tax charged directly on them), day by day.
    See module docstring for why this isn't the gross pre-tax figure.
    """
    raw = _read_raw()
    contrib = raw[
        (raw["Category"] == "CONTRIBUTIONS") | (raw["Title"].isin(CONTRIBUTION_TAX_TITLES))
    ]
    if contrib.empty:
        return pd.DataFrame(columns=["date", "amount_aud"])
    daily = contrib.groupby("Date")["Total Amount"].sum()
    return pd.DataFrame({"date": daily.index, "amount_aud": daily.values}).sort_values("date")


def total_fees_aud() -> float:
    """Lifetime administration fees paid, net of the partial tax-deductibility rebate
    the fund passes back (both share Category == FEES) — the real out-of-pocket cost,
    not the gross fee. Already AUD-native, no FX conversion needed.
    """
    raw = _read_raw()
    fees = raw[raw["Category"] == FEE_CATEGORY]
    return float(-fees["Total Amount"].sum())  # negative in the raw data; flip to a paid magnitude


def daily_aud_series(date_range: list[date]) -> pd.Series:
    """Reindexed onto `date_range`: 0 before the account's own earliest transaction,
    forward-filled across gaps and past the last entry — same pattern as
    parse_kowhai.daily_aud_series (no FX conversion needed here, already AUD).
    """
    balance = parse_daily_balance()
    if balance.empty:
        return pd.Series(0.0, index=pd.Index(date_range))
    start, end = balance["date"].min(), max(date_range)
    own_range = pd.date_range(start, end, freq="D").date
    series = balance.set_index("date")["balance_aud"].reindex(own_range).ffill()
    return series.reindex(date_range).fillna(0.0)


def daily_contributed_aud_series(date_range: list[date]) -> pd.Series:
    """Cumulative net-contributed AUD, reindexed onto `date_range` the same way as
    daily_aud_series.
    """
    contrib = parse_contributions()
    if contrib.empty:
        return pd.Series(0.0, index=pd.Index(date_range))
    start, end = contrib["date"].min(), max(date_range)
    own_range = pd.date_range(start, end, freq="D").date
    daily_delta = contrib.set_index("date")["amount_aud"].reindex(own_range, fill_value=0.0)
    cumulative = daily_delta.cumsum()
    return cumulative.reindex(date_range).fillna(0.0)


if __name__ == "__main__":
    balance = parse_daily_balance()
    start, end = balance["date"].min(), balance["date"].max()
    print(f"{len(balance)} distinct transaction dates, {start} to {end}")
    print(f"Latest reconstructed balance: AUD {balance['balance_aud'].iloc[-1]:,.2f}")

    contrib = parse_contributions()
    print(f"\nNet contributed (post-tax): AUD {contrib['amount_aud'].sum():,.2f}")

    raw = _read_raw()
    transfers = raw[raw["Title"] == DIRECT_TRANSFER_TITLE]
    print(
        f"\n{len(transfers)} 'Direct transfer' rows excluded "
        f"(internal — AUD {transfers['Total Amount'].sum():,.2f})"
    )

    print(f"\nTotal fees paid (net of tax benefit), AUD: {total_fees_aud():,.2f}")
