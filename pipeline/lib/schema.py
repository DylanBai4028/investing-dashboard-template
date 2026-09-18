"""The transaction-level schema every parser produces, and a synthetic fixture
matching it — used to build and test backfill.py/aggregate.py independent of any
real (or generated sample) export files.
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

TRANSACTION_COLUMNS = ["date", "platform", "ticker", "type", "quantity", "price", "currency"]
# type is one of: "buy", "sell", "dividend". For "dividend", `quantity` is the cash
# amount received (not a share count) and `price` is unused (kept as 0.0 for schema
# consistency).


def sample_transactions() -> pd.DataFrame:
    """Synthetic transaction history — for smoke-testing only, not the sample-data
    quickstart (see scripts/generate_sample_data.py for that). Two tickers, a few
    years of buys and one dividend each, enough to exercise backfill.py's
    holdings-as-of-date reconstruction and aggregate.py's rollups end to end.
    """
    today = date.today()
    rows = [
        {
            "date": today - timedelta(days=730),
            "platform": "Meridian",
            "ticker": "AAPL",
            "type": "buy",
            "quantity": 20,
            "price": 150.0,
            "currency": "USD",
        },
        {
            "date": today - timedelta(days=400),
            "platform": "Meridian",
            "ticker": "AAPL",
            "type": "buy",
            "quantity": 10,
            "price": 180.0,
            "currency": "USD",
        },
        {
            "date": today - timedelta(days=200),
            "platform": "Meridian",
            "ticker": "AAPL",
            "type": "dividend",
            "quantity": 12.50,
            "price": 0.0,
            "currency": "USD",
        },
        {
            "date": today - timedelta(days=100),
            "platform": "Meridian",
            "ticker": "AAPL",
            "type": "buy",
            "quantity": 5,
            "price": 220.0,
            "currency": "USD",
        },
        {
            "date": today - timedelta(days=600),
            "platform": "Northbridge",
            "ticker": "MSFT",
            "type": "buy",
            "quantity": 15,
            "price": 300.0,
            "currency": "USD",
        },
        {
            "date": today - timedelta(days=300),
            "platform": "Northbridge",
            "ticker": "MSFT",
            "type": "buy",
            "quantity": 8,
            "price": 340.0,
            "currency": "USD",
        },
        {
            "date": today - timedelta(days=150),
            "platform": "Northbridge",
            "ticker": "MSFT",
            "type": "sell",
            "quantity": 5,
            "price": 400.0,
            "currency": "USD",
        },
        {
            "date": today - timedelta(days=90),
            "platform": "Northbridge",
            "ticker": "MSFT",
            "type": "dividend",
            "quantity": 8.20,
            "price": 0.0,
            "currency": "USD",
        },
    ]
    df = pd.DataFrame(rows, columns=TRANSACTION_COLUMNS)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df
