"""Reconstructs daily net worth (AUD) for the transaction-based platforms from a
transaction log. This is what makes the dashboard's 1D-10Y/ALL range toggle real
instead of empty from day one.

Vectorized (pandas cumulative sums over a date range), not a per-day replay loop —
this runs over years of days x however many tickers you hold, which a naive loop
would make noticeably slow.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from prices import get_fx_series, get_historical_series


def holdings_by_date(transactions: pd.DataFrame, ticker: str, platform: str) -> pd.Series:
    """Cumulative share quantity held in `ticker` **on `platform`**, indexed by every
    calendar day from its first transaction to today. Buys add, sells subtract;
    dividends don't change the share count.

    Both `ticker` and `platform` matter: the same ticker can be held on more than one
    platform (e.g. a broad-market ETF on both your AU and NZ broker) as two genuinely
    separate positions, not one — every holding-level operation in this pipeline keys
    on the pair, never ticker alone.
    """
    tx = transactions[(transactions["ticker"] == ticker) & (transactions["platform"] == platform)]
    tx = tx[tx["type"].isin(["buy", "sell"])].copy()
    if tx.empty:
        return pd.Series(dtype=float)
    tx["signed_qty"] = tx.apply(
        lambda r: r["quantity"] if r["type"] == "buy" else -r["quantity"], axis=1
    )
    daily_delta = tx.groupby("date")["signed_qty"].sum()
    full_range = pd.date_range(daily_delta.index.min(), date.today(), freq="D").date
    daily_delta = daily_delta.reindex(full_range, fill_value=0.0)
    return daily_delta.cumsum()


def reconstruct_ticker_value_aud(
    transactions: pd.DataFrame, ticker: str, platform: str, currency: str
) -> pd.DataFrame:
    """Daily value of `ticker`'s holding on `platform`, in AUD, forward-filled across
    non-trading days (different markets don't share a trading calendar).
    """
    qty = holdings_by_date(transactions, ticker, platform)
    if qty.empty:
        return pd.DataFrame(columns=["date", "ticker", "value_aud"])
    start = qty.index.min()

    price_series = (
        get_historical_series(ticker, start)
        .assign(date=lambda d: pd.to_datetime(d["date"]).dt.date)
        .set_index("date")["close"]
        .reindex(qty.index)
        .ffill()
        .bfill()
    )
    # each day's own historical FX rate — never today's rate on a historical value
    fx_series = (
        get_fx_series(currency, start)
        .assign(date=lambda d: pd.to_datetime(d["date"]).dt.date)
        .set_index("date")["rate"]
        .reindex(qty.index)
        .ffill()
        .bfill()
    )
    value_native = qty * price_series
    value_aud = value_native if currency == "AUD" else value_native / fx_series
    return pd.DataFrame({"date": qty.index, "ticker": ticker, "value_aud": value_aud.values})


def daily_grand_total(daily_reconstructed: pd.DataFrame) -> pd.DataFrame:
    """Sum every ticker's daily AUD value into one total-by-date series."""
    if daily_reconstructed.empty:
        return pd.DataFrame(columns=["date", "value_aud"])
    return daily_reconstructed.groupby("date", as_index=False)["value_aud"].sum()


def contributions_over_time(transactions: pd.DataFrame) -> pd.DataFrame:
    """Cumulative net capital invested (AUD), day by day — buys add at cost, sells
    subtract at cost (not at sale price, since a sell returns capital, it doesn't
    "contribute" more). Converted using **each transaction's own date's** FX rate, same
    principle as the value backfill. Stock-only — manual/ledger assets have their own
    equivalent (see _ledger_platform in run_dashboard.py).
    """
    tx = transactions[transactions["type"].isin(["buy", "sell"])].copy()
    if tx.empty:
        return pd.DataFrame(columns=["date", "contributed_aud"])

    fx_cache: dict[str, pd.DataFrame] = {}

    def to_aud(row: pd.Series) -> float:
        cost_native = row["quantity"] * row["price"]
        if row["currency"] == "AUD":
            return cost_native
        if row["currency"] not in fx_cache:
            fx_cache[row["currency"]] = get_fx_series(row["currency"], tx["date"].min()).assign(
                date=lambda d: pd.to_datetime(d["date"]).dt.date
            )
        fx = fx_cache[row["currency"]]
        match = fx[fx["date"] == row["date"]]
        rate = match["rate"].iloc[0] if not match.empty else fx["rate"].iloc[-1]
        return cost_native / rate

    tx["cost_aud"] = tx.apply(to_aud, axis=1)
    tx["signed_cost_aud"] = tx.apply(
        lambda r: r["cost_aud"] if r["type"] == "buy" else -r["cost_aud"], axis=1
    )
    daily_delta = tx.groupby("date")["signed_cost_aud"].sum()
    full_range = pd.date_range(daily_delta.index.min(), date.today(), freq="D").date
    daily_delta = daily_delta.reindex(full_range, fill_value=0.0)
    cumulative = daily_delta.cumsum()
    return pd.DataFrame({"date": cumulative.index, "contributed_aud": cumulative.values})


def reconstruct_net_worth(transactions: pd.DataFrame) -> pd.DataFrame:
    """Daily value (AUD) for every (ticker, platform) combination in `transactions` —
    the raw material for per-platform and total daily net-worth series. Keyed on both,
    not ticker alone (see holdings_by_date's docstring).
    """
    ticker_meta = transactions[["ticker", "platform", "currency"]].drop_duplicates(
        ["ticker", "platform"]
    )
    frames = []
    for _, meta in ticker_meta.iterrows():
        df = reconstruct_ticker_value_aud(
            transactions, meta["ticker"], meta["platform"], meta["currency"]
        )
        if df.empty:
            continue
        df["platform"] = meta["platform"]
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["date", "ticker", "platform", "value_aud"])
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    from schema import sample_transactions

    tx = sample_transactions()
    print(f"{len(tx)} sample transactions, tickers: {sorted(tx['ticker'].unique())}\n")

    daily = reconstruct_net_worth(tx)
    print(f"{len(daily)} daily value rows reconstructed\n")

    print("-- Per-ticker latest value --")
    print(daily.sort_values("date").groupby("ticker").tail(1))

    print("\n-- Total portfolio value by day (last 5 days) --")
    total_by_day = daily.groupby("date")["value_aud"].sum().sort_index()
    print(total_by_day.tail())
