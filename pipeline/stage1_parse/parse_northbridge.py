"""Parses Northbridge's transactions CSV into the schema.TRANSACTION_COLUMNS shape.

Northbridge is a template stand-in for a typical NZ broker offering US market access
— one CSV covering full history (unlike Meridian's per-financial-year split):
`data/exports/northbridge-markets-transactions-report-*.csv`. Columns: Date
(DD/MM/YYYY), Transaction type, Symbol, Investment name, Description, Amount (USD),
Order fill price, Order share quantity, Order fee.

Transaction types this parser handles:
  - "Order - Buy" / "Order - Sell": real trades. `Amount (USD)` already nets the fee
    (qty * fill_price ± fee == Amount) — so `abs(Amount) / quantity` is used as the
    effective price, same principle as Meridian's `Total Value / Units`.
  - "Dividend" + "Dividend Tax": both treated as `type="dividend"` cash-flow rows —
    Dividend is positive, Dividend Tax is negative (US withholding), so summing both
    gives the net cash actually received without needing to match pairs by date.
  - "Stock Split": handled via apply_split_adjustments() below — every trade dated
    before a split gets its quantity multiplied and price divided by that split's
    ratio, chained in chronological order across multiple splits on the same ticker.
  - "Deposit": used for `load_deposits()`, same role as Meridian's CASH_TRANSACTION.
  - Excluded entirely: "Cancelled order - Buy" (Amount is $0, no real effect),
    "Interest Adjustment" and "One-off US tax fee" (cash-level, not tied to any
    holding), and dividends on cash-sweep symbols (money-market interest on
    un-invested cash, not equity income).
  - A symbol rename is handled via SYMBOL_RENAMES — a holding whose ticker changed
    partway through its history (e.g. a company renaming itself) needs its old and
    new symbols mapped to one identity before backfill/aggregate see it, or it reads
    as two separate, smaller positions instead of one real one.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"

# Tickers with a data-quality question mark still open — excluded from parse() until
# resolved, rather than guessed at.
UNRESOLVED_TICKERS: set[str] = set()

# Broker-side symbol quirks: the raw Symbol column uses an old/wrong ticker for a real
# holding after a real-world rename (see module docstring).
SYMBOL_RENAMES = {"FB": "META"}

# Cash-sweep / money-market symbols — dividends here are interest on un-invested cash,
# not equity income. Never appear in Order - Buy/Sell (nothing to hold), so they only
# need excluding from the dividend stream.
CASH_SWEEP_SYMBOLS = {"DAGXX", "DARXX"}

TRADE_TYPES = {"Order - Buy": "buy", "Order - Sell": "sell"}


def _northbridge_file() -> Path:
    matches = sorted(EXPORTS_DIR.glob("northbridge-markets-transactions-report-*.csv"))
    if not matches:
        raise FileNotFoundError(f"No Northbridge export found in {EXPORTS_DIR}")
    return matches[-1]  # most recent, if more than one is ever saved


def _read_raw() -> pd.DataFrame:
    df = pd.read_csv(_northbridge_file())
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y").dt.date
    df["Symbol"] = df["Symbol"].replace(SYMBOL_RENAMES)
    return df


def get_split_ratios(raw: pd.DataFrame) -> pd.DataFrame:
    """[date, ticker, ratio] for every Stock Split row. `ratio` = shares-after /
    shares-before, computed from the description's own numbers, not a generic "1:N"
    label — more robust than parsing the ratio text, which can carry rounding.
    """
    splits = raw[raw["Transaction type"] == "Stock Split"].copy()
    if splits.empty:
        return pd.DataFrame(columns=["date", "ticker", "ratio"])
    extracted = (
        splits["Description"].str.extract(r"([\d.]+) shares to ([\d.]+) shares").astype(float)
    )
    return pd.DataFrame(
        {
            "date": splits["Date"].values,
            "ticker": splits["Symbol"].values,
            "ratio": (extracted[1] / extracted[0]).values,
        }
    )


def apply_split_adjustments(trades: pd.DataFrame, splits: pd.DataFrame) -> pd.DataFrame:
    """Multiplies quantity (and divides price, so quantity*price stays the trade's real
    dollar value) for every trade dated *before* a split, per ticker — chaining
    multiple splits in chronological order so they compound correctly.
    """
    trades = trades.copy()
    for _, split in splits.sort_values("date").iterrows():
        mask = (trades["ticker"] == split["ticker"]) & (trades["date"] < split["date"])
        trades.loc[mask, "quantity"] *= split["ratio"]
        trades.loc[mask, "price"] /= split["ratio"]
    return trades


def load_trades(raw: pd.DataFrame | None = None) -> pd.DataFrame:
    raw = raw if raw is not None else _read_raw()
    trades = raw[raw["Transaction type"].isin(TRADE_TYPES)].copy()
    trades = trades[~trades["Symbol"].isin(UNRESOLVED_TICKERS)]
    if trades.empty:
        return pd.DataFrame(
            columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
        )
    out = pd.DataFrame(
        {
            "date": trades["Date"],
            "platform": "Northbridge",
            "ticker": trades["Symbol"],
            "type": trades["Transaction type"].map(TRADE_TYPES),
            "quantity": trades["Order share quantity"],
            "price": trades["Amount (USD)"].abs() / trades["Order share quantity"],
            "currency": "USD",
        }
    )
    return apply_split_adjustments(out, get_split_ratios(raw))


def load_dividends(raw: pd.DataFrame | None = None) -> pd.DataFrame:
    raw = raw if raw is not None else _read_raw()
    divs = raw[raw["Transaction type"].isin(["Dividend", "Dividend Tax"])].copy()
    # a handful of rows (an unattributed monthly-summary line) carry no Symbol at all —
    # excluded rather than guessed at (each is a few cents, immaterial either way)
    divs = divs.dropna(subset=["Symbol"])
    divs = divs[~divs["Symbol"].isin(CASH_SWEEP_SYMBOLS | UNRESOLVED_TICKERS)]
    if divs.empty:
        return pd.DataFrame(
            columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
        )
    return pd.DataFrame(
        {
            "date": divs["Date"],
            "platform": "Northbridge",
            "ticker": divs["Symbol"],
            "type": "dividend",
            "quantity": divs["Amount (USD)"],  # Dividend +, Dividend Tax - -> nets out
            "price": 0.0,
            "currency": "USD",
        }
    )


def load_fees(raw: pd.DataFrame | None = None) -> pd.DataFrame:
    """Every trade's Order fee — [date, currency, amount], USD, as a positive
    magnitude. Already netted into Amount (USD) for load_trades()'s cost basis, so
    this is a separate read of the raw column.
    """
    raw = raw if raw is not None else _read_raw()
    fees = raw[raw["Order fee"].notna() & (raw["Order fee"] != 0)]
    if fees.empty:
        return pd.DataFrame(columns=["date", "currency", "amount"])
    return pd.DataFrame(
        {"date": fees["Date"], "currency": "USD", "amount": fees["Order fee"].abs()}
    )


def load_deposits(raw: pd.DataFrame | None = None) -> pd.DataFrame:
    """[date, currency, amount] — for a real "total contributed" figure, same role as
    parse_meridian.load_deposits().
    """
    raw = raw if raw is not None else _read_raw()
    deposits = raw[raw["Transaction type"] == "Deposit"]
    if deposits.empty:
        return pd.DataFrame(columns=["date", "currency", "amount"])
    return pd.DataFrame(
        {"date": deposits["Date"], "currency": "USD", "amount": deposits["Amount (USD)"]}
    )


def parse() -> pd.DataFrame:
    """Full transaction log — trades + dividends, split-adjusted — ready for
    backfill.py/aggregate.py.
    """
    raw = _read_raw()
    return pd.concat([load_trades(raw), load_dividends(raw)], ignore_index=True).sort_values("date")


if __name__ == "__main__":
    raw = _read_raw()
    tx = parse()
    print(f"{len(tx)} transactions parsed: {tx['type'].value_counts().to_dict()}")
    print(f"Tickers: {sorted(tx['ticker'].unique())}")
    print(f"Date range: {tx['date'].min()} to {tx['date'].max()}")

    splits = get_split_ratios(raw)
    print(f"\n{len(splits)} stock splits applied:")
    print(splits.to_string(index=False))

    deposits = load_deposits(raw)
    print(f"\n{len(deposits)} deposits totalling USD {deposits['amount'].sum():,.2f}")
