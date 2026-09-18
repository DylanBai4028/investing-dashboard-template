"""Parses a Yahoo Finance crypto portfolio export into the schema.TRANSACTION_COLUMNS
shape.

Built against `data/exports/yahoo-crypto-portfolio.csv`. Columns include Symbol
(already yfinance-compatible, e.g. "BTC-USD"), Trade Date (YYYYMMDD), Purchase Price,
Quantity, Transaction Type (BUY/SELL) — a per-lot format, one row per trade.

`yfinance` supports historical crypto prices directly via this same "XXX-USD" ticker
format, so crypto goes through the exact same backfill.py reconstruction as stocks —
full historical net worth, not just a current-price snapshot.

Rows with no Transaction Type (no Trade Date/Purchase Price/Quantity either) are
watchlist-only entries, not real holdings — excluded.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"

TRADE_TYPES = {"BUY": "buy", "SELL": "sell"}


def _crypto_file() -> Path:
    matches = sorted(EXPORTS_DIR.glob("yahoo-crypto-portfolio.csv"))
    if not matches:
        raise FileNotFoundError(f"No crypto export found in {EXPORTS_DIR}")
    return matches[-1]


def parse() -> pd.DataFrame:
    raw = pd.read_csv(_crypto_file())
    real = raw[raw["Transaction Type"].isin(TRADE_TYPES)].copy()
    if real.empty:
        return pd.DataFrame(
            columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
        )
    return pd.DataFrame(
        {
            "date": pd.to_datetime(real["Trade Date"], format="%Y%m%d").dt.date,
            "platform": "Crypto",
            "ticker": real["Symbol"],  # already "BTC-USD" etc. — yfinance-compatible
            "type": real["Transaction Type"].map(TRADE_TYPES),
            "quantity": real["Quantity"],
            "price": real["Purchase Price"],
            "currency": "USD",
        }
    ).sort_values("date")


if __name__ == "__main__":
    tx = parse()
    print(f"{len(tx)} transactions parsed: {tx['type'].value_counts().to_dict()}")
    print(f"Tickers: {sorted(tx['ticker'].unique())}")

    print("\nNet quantity per coin (buys - sells):")
    for ticker, g in tx.groupby("ticker"):
        buys = g[g["type"] == "buy"]["quantity"].sum()
        sells = g[g["type"] == "sell"]["quantity"].sum()
        net = buys - sells
        status = "EXITED" if abs(net) < 1e-9 else f"{net:.6f}"
        print(f"  {ticker:10} {status}")
