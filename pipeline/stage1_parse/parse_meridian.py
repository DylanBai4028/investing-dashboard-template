"""Parses Meridian's exported reports into the schema.TRANSACTION_COLUMNS shape.

Meridian is a template stand-in for a typical AU share broker — five report types per
financial year, in data/exports/, all prefixed MERIDIAN_ (produced by
scripts/generate_sample_data.py for this template; swap in your own broker's real
exports and adjust the column mapping below to match):
  - INVESTMENT_ACTIVITY: buy/sell trades. Sheets "Aus Equities" / "Wall St Equities",
    columns [Trade Date, Settlement Date, Symbol, Name, Side, Trade Identifier, Units,
    Avg. Price, Value, Fees, GST, Total Value, Currency].
  - INVESTMENT_INCOME: dividends, in a SEPARATE report from buys/sells (not mixed in).
    Sheets "Aus Dividends (Estimated)" / "Wall St Dividends" — different columns each.
  - PORTFOLIO_VALUATION: a point-in-time holdings snapshot (symbol, units, market
    value) — not used for the transaction log, but as a cross-check (see
    cross_check_against_valuation) against holdings reconstructed purely from
    INVESTMENT_ACTIVITY.
  - CASH_TRANSACTION: deposits — a more accurate "money contributed" source than
    inferring it from buy costs (also correctly counts un-invested cash).
  - OTHER_ACTIVITY: transfers/corporate actions, not used by this template.

Buy/sell cost basis uses `Total Value / Units` (not `Avg. Price`) as the effective
price, since Total Value already folds in Fees and GST — Avg. Price alone understates
the real cost.

One ticker in the sample data (COIN) arrives with no purchase transaction on record —
a referral/reward share, not a real buy — handled via GIFTED_COST_BASIS_ZERO below
rather than left silently missing from holdings.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).parent.parent.parent / "data" / "exports"

# Tickers known to have entered the account with no purchase transaction on record
# (gifted/referral shares) — cost basis is $0 for these rather than "unknown", since
# the platform gave them away, not sold them.
GIFTED_COST_BASIS_ZERO = {"COIN"}


def _meridian_files(prefix: str) -> list[Path]:
    return sorted(EXPORTS_DIR.glob(f"MERIDIAN_{prefix}_*.xlsx"))


def _read_equities_sheet(path: Path, sheet: str, is_au: bool) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet, engine="calamine")
    if df.empty:
        return pd.DataFrame(
            columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
        )
    ticker = df["Symbol"].str.strip() + (".AX" if is_au else "")
    return pd.DataFrame(
        {
            "date": pd.to_datetime(df["Trade Date"]).dt.date,
            "platform": "Meridian",
            "ticker": ticker,
            "type": df["Side"].str.lower(),  # "Buy" / "Sell" -> "buy" / "sell"
            "quantity": df["Units"],
            "price": df["Total Value"] / df["Units"],  # includes fees/GST, see docstring
            "currency": df["Currency"],
        }
    )


def load_trades() -> pd.DataFrame:
    """Every buy/sell across all MERIDIAN_INVESTMENT_ACTIVITY_*.xlsx files, deduped on
    (date, ticker, type, quantity, price) in case financial-year exports ever overlap.
    """
    frames = []
    for path in _meridian_files("INVESTMENT_ACTIVITY"):
        frames.append(_read_equities_sheet(path, "Aus Equities", is_au=True))
        frames.append(_read_equities_sheet(path, "Wall St Equities", is_au=False))
    if not frames:
        return pd.DataFrame(
            columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
        )
    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(subset=["date", "ticker", "type", "quantity", "price"])


def load_dividends() -> pd.DataFrame:
    """Every dividend across all MERIDIAN_INVESTMENT_INCOME_*.xlsx files, as `type` =
    "dividend" rows matching schema.TRANSACTION_COLUMNS (quantity holds the cash
    amount received, price is unused — see schema.py).

    Uses Net Amount (after US withholding tax) for Wall St dividends — the cash that
    actually landed, not the gross figure — and Total Amount for AU dividends (no
    separate net-of-withholding column; AU dividends aren't withheld at source the
    same way).
    """
    frames = []
    for path in _meridian_files("INVESTMENT_INCOME"):
        au = pd.read_excel(path, sheet_name="Aus Dividends (Estimated)", engine="calamine")
        if not au.empty:
            frames.append(
                pd.DataFrame(
                    {
                        "date": pd.to_datetime(au["Payment Date"]).dt.date,
                        "platform": "Meridian",
                        "ticker": au["Symbol"].str.strip() + ".AX",
                        "type": "dividend",
                        "quantity": au["Total Amount"],
                        "price": 0.0,
                        "currency": "AUD",
                    }
                )
            )
        us = pd.read_excel(path, sheet_name="Wall St Dividends", engine="calamine")
        if not us.empty:
            frames.append(
                pd.DataFrame(
                    {
                        "date": pd.to_datetime(us["Payment Date"]).dt.date,
                        "platform": "Meridian",
                        "ticker": us["Symbol"].str.strip(),
                        "type": "dividend",
                        "quantity": us["Net Amount"],
                        "price": 0.0,
                        "currency": us["Currency"],
                    }
                )
            )
    if not frames:
        return pd.DataFrame(
            columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
        )
    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(subset=["date", "ticker", "quantity"])


def load_gifted_shares() -> pd.DataFrame:
    """Synthetic zero-cost "buy" rows for tickers in GIFTED_COST_BASIS_ZERO that have
    no real purchase transaction on record, dated at the earliest date they appear in
    a PORTFOLIO_VALUATION snapshot — so they show up in holdings/backfill at all, with
    an honest $0 cost basis rather than silently missing.
    """
    valuations = load_portfolio_valuations()
    if valuations.empty:
        return pd.DataFrame(
            columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
        )
    rows = []
    for ticker in GIFTED_COST_BASIS_ZERO:
        seen = valuations[valuations["ticker"] == ticker]
        if seen.empty:
            continue
        first = seen.sort_values("date").iloc[0]
        rows.append(
            {
                "date": first["date"],
                "platform": "Meridian",
                "ticker": ticker,
                "type": "buy",
                "quantity": first["units"],
                "price": 0.0,
                "currency": "USD",
            }
        )
    return pd.DataFrame(
        rows, columns=["date", "platform", "ticker", "type", "quantity", "price", "currency"]
    )


def load_fees() -> pd.DataFrame:
    """Every trade's Fees + GST across all MERIDIAN_INVESTMENT_ACTIVITY_*.xlsx files —
    [date, currency, amount] — already excluded from load_trades()'s cost-basis price
    (see this module's docstring: Total Value folds Fees/GST in), so this is a separate
    read of the raw sheet, not derived from load_trades()'s output.
    """
    frames = []
    for path in _meridian_files("INVESTMENT_ACTIVITY"):
        for sheet, currency in (("Aus Equities", "AUD"), ("Wall St Equities", "USD")):
            df = pd.read_excel(path, sheet_name=sheet, engine="calamine")
            if df.empty:
                continue
            frames.append(
                pd.DataFrame(
                    {
                        "date": pd.to_datetime(df["Trade Date"]).dt.date,
                        "currency": currency,
                        "amount": df["Fees"].fillna(0.0) + df["GST"].fillna(0.0),
                    }
                )
            )
    if not frames:
        return pd.DataFrame(columns=["date", "currency", "amount"])
    return pd.concat(frames, ignore_index=True)


def load_deposits() -> pd.DataFrame:
    """Every deposit across all MERIDIAN_CASH_TRANSACTION_*.xlsx files — [date,
    currency, amount]. Used for a real "total contributed" figure instead of
    inferring it from buy costs (see aggregate.py).
    """
    frames = []
    for path in _meridian_files("CASH_TRANSACTION"):
        for sheet in ("AUD", "USD"):
            df = pd.read_excel(path, sheet_name=sheet, engine="calamine")
            if df.empty:
                continue
            deposits = df[df["Transaction"].str.contains("deposit", case=False, na=False)]
            if not deposits.empty:
                frames.append(
                    pd.DataFrame(
                        {
                            "date": pd.to_datetime(deposits["Date"]).dt.date,
                            "currency": deposits["Currency"],
                            "amount": deposits["Credit"],
                        }
                    )
                )
    if not frames:
        return pd.DataFrame(columns=["date", "currency", "amount"])
    return pd.concat(frames, ignore_index=True)


def load_portfolio_valuations() -> pd.DataFrame:
    """Every point-in-time holdings snapshot across all
    MERIDIAN_PORTFOLIO_VALUATION_*.xlsx files — [date, ticker, units, value_native,
    currency]. Cross-check material, not a dashboard data source.
    """
    frames = []
    for path in _meridian_files("PORTFOLIO_VALUATION"):
        m = re.search(r"PORTFOLIO_VALUATION_(\d{4}-\d{2}-\d{2})", path.name)
        as_of = pd.to_datetime(m.group(1)).date()
        au = pd.read_excel(path, sheet_name="Aus Equities", engine="calamine")
        if not au.empty:
            frames.append(
                pd.DataFrame(
                    {
                        "date": as_of,
                        "ticker": au["Symbol"].str.strip() + ".AX",
                        "units": au["Units"],
                        "value_native": au["Mkt. Value"],
                        "currency": "AUD",
                    }
                )
            )
        us = pd.read_excel(path, sheet_name="Wall St Equities", engine="calamine")
        if not us.empty:
            frames.append(
                pd.DataFrame(
                    {
                        "date": as_of,
                        "ticker": us["Symbol"].str.strip(),
                        "units": us["Units"],
                        "value_native": us["Mkt. Value (US$)"],
                        "currency": "USD",
                    }
                )
            )
    if not frames:
        return pd.DataFrame(columns=["date", "ticker", "units", "value_native", "currency"])
    return pd.concat(frames, ignore_index=True)


def parse() -> pd.DataFrame:
    """Full transaction log — trades + dividends + gifted-share entries — ready for
    backfill.py/aggregate.py.
    """
    return pd.concat(
        [load_trades(), load_dividends(), load_gifted_shares()], ignore_index=True
    ).sort_values("date")


def cross_check_against_valuation(transactions: pd.DataFrame) -> pd.DataFrame:
    """Compares reconstructed holdings (from `transactions`) against the latest
    PORTFOLIO_VALUATION snapshot. Returns rows where they disagree by more than a
    trivial rounding amount — an empty result means the transaction log fully explains
    the platform's own record of what you hold. An internal consistency check between
    two different reports the same platform provides, not just "did the code run
    without an error."
    """
    valuations = load_portfolio_valuations()
    if valuations.empty:
        return pd.DataFrame()
    latest_date = valuations["date"].max()
    latest = valuations[valuations["date"] == latest_date]

    trades = transactions[transactions["type"].isin(["buy", "sell"])]
    signed = trades.assign(
        signed_qty=trades.apply(
            lambda r: r["quantity"] if r["type"] == "buy" else -r["quantity"], axis=1
        )
    )
    reconstructed = signed.groupby("ticker")["signed_qty"].sum().rename("reconstructed_units")

    merged = latest.set_index("ticker")[["units"]].join(reconstructed, how="outer").fillna(0.0)
    merged["diff"] = merged["units"] - merged["reconstructed_units"]
    return merged[merged["diff"].abs() > 0.01]


if __name__ == "__main__":
    tx = parse()
    print(f"{len(tx)} transactions parsed: {tx['type'].value_counts().to_dict()}")
    print(f"Tickers: {sorted(tx['ticker'].unique())}")
    print(f"Date range: {tx['date'].min()} to {tx['date'].max()}")

    deposits = load_deposits()
    by_currency = deposits.groupby("currency")["amount"].sum().to_dict()
    print(f"\n{len(deposits)} deposits, by currency: {by_currency}")

    mismatches = cross_check_against_valuation(tx)
    if mismatches.empty:
        print("\nCross-check vs. latest PORTFOLIO_VALUATION: no discrepancies.")
    else:
        print("\nCross-check vs. latest PORTFOLIO_VALUATION: DISCREPANCIES FOUND")
        print(mismatches.to_string())
