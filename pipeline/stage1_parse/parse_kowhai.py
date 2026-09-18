"""Parses Kowhai's transaction-ledger export into a real daily NZD balance series and
a contributions series.

Kowhai is a template stand-in for a typical NZ KiwiSaver-style managed fund. Built
against `data/exports/Kowhai-transactions.csv`: a running ledger — [Date, Transaction
details, debits, Credits, Balance] — ordered newest-row-first.

Two things this unlocks that a flat manual snapshot couldn't:
  - A genuine daily balance history (the `Balance` column is already a running total
    in dollar terms — no price/quantity reconstruction needed, unlike stocks), so
    Kowhai contributes a real line to the net-worth-over-time chart instead of a
    coarse step function.
  - A real "total contributed" figure. The transaction detail types split cleanly into
    contributions (new capital: "Your contributions", "Employer contributions",
    "Transfer in ..." variants, "Government contribution") versus returns/costs
    (investment earnings, PIE tax, admin fees) — the CONTRIBUTION_TYPES set below is
    exactly this split. Employer/government contributions and an IRD kick-start
    transfer are all KiwiSaver-specific, consistent with treating this as illiquid-
    style infrastructure even though this template counts it as liquid (see
    config.ILLIQUID_PLATFORMS's comment for why).
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# Bootstrap: this file lives in pipeline/stage1_parse/, a sibling of pipeline/lib/ —
# needed so `from prices import get_fx_series` below resolves both when this module
# is imported (from stage2_generate/run_dashboard.py, which sets this up itself too —
# harmless to repeat) and when it's run standalone for its own __main__ smoke test.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import pandas as pd  # noqa: E402
from prices import get_fx_series  # noqa: E402

EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"

CONTRIBUTION_TYPES = {
    "Your contributions",
    "Employer contributions",
    "Government contribution",
    "Transfer in your contributions",
    "Transfer in employer contributions",
    "Transfer in government contribution",
    "Transfer in IRD kick-start",
}

# The only genuine fee line item in this ledger — "PIE tax at your PIR" is a tax, not a
# fee, and isn't counted here (see parse_fees()'s docstring for why).
FEE_TYPES = {"Administration fees"}


def _kowhai_file() -> Path:
    matches = sorted(EXPORTS_DIR.glob("Kowhai-transactions.csv"))
    if not matches:
        raise FileNotFoundError(f"No Kowhai export found in {EXPORTS_DIR}")
    return matches[-1]


def _read_raw() -> pd.DataFrame:
    df = pd.read_csv(_kowhai_file())
    df["Date"] = pd.to_datetime(df["Date"], format="%d %b %Y").dt.date
    df["Balance"] = df["Balance"].replace(r"[$,]", "", regex=True).astype(float)
    for col in ("debits", "Credits"):
        # empty cells parse as NaN (a float), not "" (a string) — go through str first
        # so NaN becomes matchable by the regex replace, then fillna, or a plain
        # .replace("", "0") never matches NaN and it silently propagates through the
        # later Credits - debits subtraction.
        cleaned = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
        df[col] = pd.to_numeric(cleaned, errors="coerce").fillna(0.0)
    return df


def parse_daily_balance() -> pd.DataFrame:
    """[date, balance_nzd] — one row per distinct date, using that date's *last*
    posted balance. The file lists rows newest-first overall; taking each date's
    first occurrence when scanning top-to-bottom is exactly the same thing as taking
    its temporally-last posting.
    """
    raw = _read_raw()
    daily = raw.groupby("Date", sort=False)["Balance"].first()
    return pd.DataFrame({"date": daily.index, "balance_nzd": daily.values}).sort_values("date")


def parse_contributions() -> pd.DataFrame:
    """[date, amount_nzd] — new capital only (contributions/transfers), not investment
    earnings, tax, or fees. Cumulative sum of this is a real "total contributed" figure
    for Kowhai.
    """
    raw = _read_raw()
    contrib = raw[raw["Transaction details"].isin(CONTRIBUTION_TYPES)]
    if contrib.empty:
        return pd.DataFrame(columns=["date", "amount_nzd"])
    amounts = contrib["Credits"] - contrib["debits"]
    return pd.DataFrame({"date": contrib["Date"], "amount_nzd": amounts}).sort_values("date")


def parse_fees() -> pd.DataFrame:
    """[date, amount_nzd] — administration fees only, as a positive magnitude (money
    that actually left the account). "PIE tax at your PIR" is excluded deliberately:
    it's investment income tax, not a cost of running the fund.
    """
    raw = _read_raw()
    fees = raw[raw["Transaction details"].isin(FEE_TYPES)]
    if fees.empty:
        return pd.DataFrame(columns=["date", "amount_nzd"])
    # debits is already stored negative (e.g. "-$0.23") — Credits is 0/NaN for a fee
    # row, so Credits - debits correctly yields the positive amount paid.
    amounts = fees["Credits"] - fees["debits"]
    return pd.DataFrame({"date": fees["Date"], "amount_nzd": amounts}).sort_values("date")


def total_fees_aud() -> float:
    """Lifetime administration fees paid, converted to AUD using each fee's own date's
    historical NZD/AUD rate (never today's rate on a historical value).
    """
    fees = parse_fees()
    if fees.empty:
        return 0.0
    start = fees["date"].min()
    fx = get_fx_series("NZD", start).assign(date=lambda d: pd.to_datetime(d["date"]).dt.date)
    fx_series = fx.set_index("date")["rate"]
    rates = fx_series.reindex(fees["date"]).ffill().bfill()
    return float((fees["amount_nzd"].values / rates.values).sum())


def daily_aud_series(date_range: list[date]) -> pd.Series:
    """Kowhai's daily balance, converted to AUD using each date's own historical
    NZD/AUD rate (never today's rate on a past value), reindexed onto `date_range`. 0
    before the ledger's own earliest date (not tracked yet, not a zero balance);
    forward-filled across gaps between real postings and past its last entry.
    """
    balance = parse_daily_balance()
    if balance.empty:
        return pd.Series(0.0, index=pd.Index(date_range))
    start = balance["date"].min()
    end = max(date_range)
    own_range = pd.date_range(start, end, freq="D").date

    fx = get_fx_series("NZD", start).assign(date=lambda d: pd.to_datetime(d["date"]).dt.date)
    fx_series = fx.set_index("date")["rate"].reindex(own_range).ffill().bfill()
    bal_series = balance.set_index("date")["balance_nzd"].reindex(own_range).ffill()

    aud_series = bal_series / fx_series
    return aud_series.reindex(date_range).fillna(0.0)


def daily_contributed_aud_series(date_range: list[date]) -> pd.Series:
    """Cumulative real contributions (AUD), same reindexing/conversion principles as
    daily_aud_series above — Kowhai's equivalent of backfill.contributions_over_time.
    """
    contrib = parse_contributions()
    if contrib.empty:
        return pd.Series(0.0, index=pd.Index(date_range))
    start = contrib["date"].min()
    end = max(date_range)
    own_range = pd.date_range(start, end, freq="D").date

    daily_delta = contrib.groupby("date")["amount_nzd"].sum().reindex(own_range, fill_value=0.0)
    cumulative_nzd = daily_delta.cumsum()

    fx = get_fx_series("NZD", start).assign(date=lambda d: pd.to_datetime(d["date"]).dt.date)
    fx_series = fx.set_index("date")["rate"].reindex(own_range).ffill().bfill()

    cumulative_aud = cumulative_nzd / fx_series
    return cumulative_aud.reindex(date_range).fillna(0.0)


if __name__ == "__main__":
    balance = parse_daily_balance()
    print(f"{len(balance)} distinct dates, {balance['date'].min()} to {balance['date'].max()}")
    print(f"Latest balance: NZD {balance['balance_nzd'].iloc[-1]:,.2f}")

    contrib = parse_contributions()
    total_contributed = contrib["amount_nzd"].sum()
    print(f"\n{len(contrib)} contribution events, totalling NZD {total_contributed:,.2f}")

    fees = parse_fees()
    print(f"\n{len(fees)} fee events, totalling NZD {fees['amount_nzd'].sum():,.2f}")
    print(f"Total fees paid, AUD: {total_fees_aud():,.2f}")
