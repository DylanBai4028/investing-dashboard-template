"""Generates synthetic broker/fund export files for the "try it in 60 seconds"
quickstart — see the README.

Produces fictional data matching each platform's real export *format* (same sheet
names, same columns), with entirely made-up holdings, dates, and dollar amounts. None
of this represents any real person's portfolio. Total ending value is approximately
$2,000,000 AUD, split across the five platforms in a deliberately illustrative
proportion — actual totals will vary a little run to run, since holding values are
priced live against real (public) market data once the pipeline runs.

Run this once before the pipeline:

    python scripts/generate_sample_data.py
    python pipeline/stage2_generate/run_dashboard.py

To try your own real data instead, drop your own exports into data/exports/ (see
"Adapting this to your own platforms" in the README) and skip this script entirely.
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

EXPORTS_DIR = Path(__file__).parent.parent / "data" / "exports"

TODAY = date.today()
FY_TAG = f"{TODAY.year}"
# The portfolio-valuation snapshot's own date, deliberately in the past (not today) —
# COIN's gifted-share "buy" (see write_meridian) is dated to this snapshot's earliest
# appearance, and needs enough trailing real price history for the pipeline's
# forward-fill to have something to fill from near the most recent trading day.
VALUATION_DATE = TODAY - timedelta(days=90)

# Per-platform scale factors, tuned so the whole portfolio lands at roughly $2M AUD
# with a deliberately different allocation split than any real reference portfolio
# (more super/fund-weighted, less brokerage-weighted). Applied to quantities/dollar
# amounts uniformly within each platform, so per-unit prices stay realistic and
# cross-platform totals stay internally consistent (e.g. a valuation snapshot's units
# still match its trades' units exactly).
SCALE_MERIDIAN = 1.22
SCALE_NORTHBRIDGE = 1.13
SCALE_CRYPTO = 0.72
SCALE_KOWHAI = 3.1
SCALE_SOUTHERNCROSS = 1.81


def _write_xlsx(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)


def _scale(df: pd.DataFrame, cols: list[str], factor: float, round_int: list[str] = []) -> pd.DataFrame:
    """Scale the given columns by `factor` in place, rounding `round_int` columns to
    whole numbers afterward (share/unit counts) — keeps per-unit prices realistic
    while scaling the overall dollar size of a platform.
    """
    df = df.copy()
    for col in cols:
        df[col] = df[col] * factor
    for col in round_int:
        df[col] = df[col].round().astype(int)
    return df


# ---------------------------------------------------------------------------
# Meridian (AU broker) — five report types, same shape as parse_meridian.py expects.
# ---------------------------------------------------------------------------
def write_meridian() -> None:
    au_trades = pd.DataFrame(
        [
            {"Trade Date": "2022-11-03", "Symbol": "CBA", "Side": "Buy", "Units": 220,
             "Total Value": 33990.00, "Currency": "AUD", "Fees": 19.95, "GST": 2.00},
            {"Trade Date": "2023-06-14", "Symbol": "CBA", "Side": "Buy", "Units": 80,
             "Total Value": 13040.00, "Currency": "AUD", "Fees": 9.95, "GST": 1.00},
            {"Trade Date": "2022-08-22", "Symbol": "BHP", "Side": "Buy", "Units": 500,
             "Total Value": 20250.00, "Currency": "AUD", "Fees": 19.95, "GST": 2.00},
            {"Trade Date": "2024-02-09", "Symbol": "BHP", "Side": "Buy", "Units": 300,
             "Total Value": 12960.00, "Currency": "AUD", "Fees": 9.95, "GST": 1.00},
        ]
    )
    us_trades = pd.DataFrame(
        [
            {"Trade Date": "2022-09-12", "Symbol": "AAPL", "Side": "Buy", "Units": 150,
             "Total Value": 22350.00, "Currency": "USD", "Fees": 0.0, "GST": 0.0},
            {"Trade Date": "2023-11-20", "Symbol": "AAPL", "Side": "Buy", "Units": 60,
             "Total Value": 11940.00, "Currency": "USD", "Fees": 0.0, "GST": 0.0},
            {"Trade Date": "2023-01-18", "Symbol": "MSFT", "Side": "Buy", "Units": 90,
             "Total Value": 22590.00, "Currency": "USD", "Fees": 0.0, "GST": 0.0},
            {"Trade Date": "2024-05-06", "Symbol": "MSFT", "Side": "Buy", "Units": 40,
             "Total Value": 16720.00, "Currency": "USD", "Fees": 0.0, "GST": 0.0},
        ]
    )
    au_trades = _scale(au_trades, ["Units", "Total Value", "Fees", "GST"], SCALE_MERIDIAN, ["Units"])
    us_trades = _scale(us_trades, ["Units", "Total Value", "Fees", "GST"], SCALE_MERIDIAN, ["Units"])
    _write_xlsx(
        EXPORTS_DIR / f"MERIDIAN_INVESTMENT_ACTIVITY_{FY_TAG}.xlsx",
        {"Aus Equities": au_trades, "Wall St Equities": us_trades},
    )

    au_divs = pd.DataFrame(
        [
            {"Payment Date": "2023-09-15", "Symbol": "CBA", "Total Amount": 660.00},
            {"Payment Date": "2024-03-15", "Symbol": "CBA", "Total Amount": 700.00},
            {"Payment Date": "2023-09-25", "Symbol": "BHP", "Total Amount": 410.00},
        ]
    )
    us_divs = pd.DataFrame(
        [
            {"Payment Date": "2023-11-16", "Symbol": "AAPL", "Net Amount": 36.00, "Currency": "USD"},
            {"Payment Date": "2024-08-15", "Symbol": "MSFT", "Net Amount": 58.50, "Currency": "USD"},
        ]
    )
    au_divs = _scale(au_divs, ["Total Amount"], SCALE_MERIDIAN)
    us_divs = _scale(us_divs, ["Net Amount"], SCALE_MERIDIAN)
    _write_xlsx(
        EXPORTS_DIR / f"MERIDIAN_INVESTMENT_INCOME_{FY_TAG}.xlsx",
        {"Aus Dividends (Estimated)": au_divs, "Wall St Dividends": us_divs},
    )

    # Valuation snapshot — units derived from the (already-scaled) trades above, so the
    # cross-check against reconstructed holdings passes exactly — plus COIN, the
    # gifted/referral share with no purchase transaction anywhere (see
    # GIFTED_COST_BASIS_ZERO). Per-share prices here are illustrative, not live.
    au_val = pd.DataFrame(
        [
            {"Symbol": "CBA", "Units": int(au_trades[au_trades["Symbol"] == "CBA"]["Units"].sum()),
             "Mkt. Value": int(au_trades[au_trades["Symbol"] == "CBA"]["Units"].sum()) * 165.0},
            {"Symbol": "BHP", "Units": int(au_trades[au_trades["Symbol"] == "BHP"]["Units"].sum()),
             "Mkt. Value": int(au_trades[au_trades["Symbol"] == "BHP"]["Units"].sum()) * 44.0},
        ]
    )
    us_val = pd.DataFrame(
        [
            {"Symbol": "AAPL", "Units": int(us_trades[us_trades["Symbol"] == "AAPL"]["Units"].sum()),
             "Mkt. Value (US$)": int(us_trades[us_trades["Symbol"] == "AAPL"]["Units"].sum()) * 230.0},
            {"Symbol": "MSFT", "Units": int(us_trades[us_trades["Symbol"] == "MSFT"]["Units"].sum()),
             "Mkt. Value (US$)": int(us_trades[us_trades["Symbol"] == "MSFT"]["Units"].sum()) * 420.0},
            {"Symbol": "COIN", "Units": round(25 * SCALE_MERIDIAN), "Mkt. Value (US$)": round(25 * SCALE_MERIDIAN) * 210.0},
        ]
    )
    _write_xlsx(
        EXPORTS_DIR / f"MERIDIAN_PORTFOLIO_VALUATION_{VALUATION_DATE.isoformat()}.xlsx",
        {"Aus Equities": au_val, "Wall St Equities": us_val},
    )

    cash_aud = pd.DataFrame(
        [
            {"Date": "2022-08-01", "Transaction": "Deposit", "Currency": "AUD", "Credit": 55000.00},
            {"Date": "2023-06-01", "Transaction": "Deposit", "Currency": "AUD", "Credit": 15000.00},
        ]
    )
    cash_usd = pd.DataFrame(
        [
            {"Date": "2022-09-01", "Transaction": "Deposit", "Currency": "USD", "Credit": 34000.00},
            {"Date": "2023-11-01", "Transaction": "Deposit", "Currency": "USD", "Credit": 20000.00},
        ]
    )
    cash_aud = _scale(cash_aud, ["Credit"], SCALE_MERIDIAN)
    cash_usd = _scale(cash_usd, ["Credit"], SCALE_MERIDIAN)
    _write_xlsx(
        EXPORTS_DIR / f"MERIDIAN_CASH_TRANSACTION_{FY_TAG}.xlsx",
        {"AUD": cash_aud, "USD": cash_usd},
    )

    # Empty on purpose — this report type exists in the real platform's export set but
    # this template has nothing to put in it (see parse_meridian.py's docstring).
    _write_xlsx(
        EXPORTS_DIR / f"MERIDIAN_OTHER_ACTIVITY_{FY_TAG}.xlsx",
        {"Activity": pd.DataFrame(columns=["Date", "Description"])},
    )


# ---------------------------------------------------------------------------
# Northbridge (NZ broker) — one CSV, real-world stock-split and symbol-rename events
# (NVDA's real 2024 10:1 split, and Facebook's real 2022 rename to Meta) reused here
# because they're genuine public market history, not personal information — a
# realistic way to exercise apply_split_adjustments() and SYMBOL_RENAMES for real.
# ---------------------------------------------------------------------------
def write_northbridge() -> None:
    rows = [
        {"Date": "15/01/2023", "Transaction type": "Order - Buy", "Symbol": "NVDA",
         "Investment name": "NVIDIA Corp", "Description": "", "Amount (USD)": -22000.00,
         "Order fill price": 220.00, "Order share quantity": 100, "Order fee": 5.00},
        {"Date": "10/06/2024", "Transaction type": "Stock Split", "Symbol": "NVDA",
         "Investment name": "NVIDIA Corp", "Description": "1 shares to 10 shares",
         "Amount (USD)": 0.0, "Order fill price": None, "Order share quantity": None, "Order fee": None},
        {"Date": "02/08/2024", "Transaction type": "Order - Buy", "Symbol": "NVDA",
         "Investment name": "NVIDIA Corp", "Description": "", "Amount (USD)": -6000.00,
         "Order fill price": 120.00, "Order share quantity": 50, "Order fee": 5.00},
        {"Date": "22/03/2022", "Transaction type": "Order - Buy", "Symbol": "FB",
         "Investment name": "Meta Platforms Inc", "Description": "", "Amount (USD)": -12858.60,
         "Order fill price": 214.31, "Order share quantity": 60, "Order fee": 5.00},
        {"Date": "11/04/2023", "Transaction type": "Order - Buy", "Symbol": "AMZN",
         "Investment name": "Amazon.com Inc", "Description": "", "Amount (USD)": -16000.00,
         "Order fill price": 200.00, "Order share quantity": 80, "Order fee": 5.00},
        {"Date": "16/11/2023", "Transaction type": "Dividend", "Symbol": "NVDA",
         "Investment name": "NVIDIA Corp", "Description": "", "Amount (USD)": 12.50,
         "Order fill price": None, "Order share quantity": None, "Order fee": None},
        {"Date": "20/11/2023", "Transaction type": "Dividend Tax", "Symbol": "NVDA",
         "Investment name": "NVIDIA Corp", "Description": "", "Amount (USD)": -1.90,
         "Order fill price": None, "Order share quantity": None, "Order fee": None},
        {"Date": "01/09/2022", "Transaction type": "Deposit", "Symbol": None,
         "Investment name": None, "Description": "", "Amount (USD)": 40000.00,
         "Order fill price": None, "Order share quantity": None, "Order fee": None},
        {"Date": "01/04/2023", "Transaction type": "Deposit", "Symbol": None,
         "Investment name": None, "Description": "", "Amount (USD)": 15000.00,
         "Order fill price": None, "Order share quantity": None, "Order fee": None},
    ]
    df = pd.DataFrame(rows)
    for col in ("Amount (USD)", "Order share quantity"):
        df[col] = df[col] * SCALE_NORTHBRIDGE
    df.to_csv(EXPORTS_DIR / f"northbridge-markets-transactions-report-{TODAY.isoformat()}.csv", index=False)


# ---------------------------------------------------------------------------
# Crypto (self-custody wallet) — Yahoo Finance portfolio-export format, unchanged
# from the real pipeline (this format isn't platform-specific, so no renaming needed).
# ---------------------------------------------------------------------------
def write_crypto() -> None:
    rows = [
        {"Symbol": "BTC-USD", "Trade Date": "20230314", "Purchase Price": 24500.00,
         "Quantity": 0.8, "Transaction Type": "BUY"},
        {"Symbol": "BTC-USD", "Trade Date": "20240122", "Purchase Price": 41200.00,
         "Quantity": 0.4, "Transaction Type": "BUY"},
        {"Symbol": "ETH-USD", "Trade Date": "20230502", "Purchase Price": 1900.00,
         "Quantity": 10.0, "Transaction Type": "BUY"},
        {"Symbol": "ETH-USD", "Trade Date": "20240610", "Purchase Price": 3400.00,
         "Quantity": 5.0, "Transaction Type": "BUY"},
        {"Symbol": "SOL-USD", "Trade Date": "20230815", "Purchase Price": 24.00,
         "Quantity": 200.0, "Transaction Type": "BUY"},
        # a fully-exited position — bought and sold the exact same quantity, nets to
        # zero and naturally drops out of current holdings without special-casing
        {"Symbol": "DOGE-USD", "Trade Date": "20230201", "Purchase Price": 0.08,
         "Quantity": 50000.0, "Transaction Type": "BUY"},
        {"Symbol": "DOGE-USD", "Trade Date": "20231110", "Purchase Price": 0.075,
         "Quantity": 50000.0, "Transaction Type": "SELL"},
    ]
    df = pd.DataFrame(rows)
    df["Quantity"] = df["Quantity"] * SCALE_CRYPTO
    df.to_csv(EXPORTS_DIR / "yahoo-crypto-portfolio.csv", index=False)


# ---------------------------------------------------------------------------
# Kowhai (NZ KiwiSaver-style fund) — running-balance ledger, newest row first, same
# shape as parse_kowhai.py expects.
# ---------------------------------------------------------------------------
def write_kowhai() -> None:
    # Built forward chronologically, then reversed to match the real export's
    # newest-first ordering.
    events = [
        ("28 Dec 2020", "Opening balance", 0.0, 0.0, 0.0),
        ("15 Jan 2021", "Your contributions", 0.0, 800.0, 800.0),
        ("15 Jan 2021", "Employer contributions", 0.0, 600.0, 1400.0),
        ("15 Jan 2021", "Government contribution", 0.0, 521.43, 1921.43),
        ("15 Jan 2021", "Transfer in IRD kick-start", 0.0, 1000.0, 2921.43),
        ("30 Jun 2021", "Investment earnings", 0.0, 145.20, 3066.63),
        ("31 Dec 2021", "Administration fees", 18.50, 0.0, 3048.13),
        ("15 Jan 2022", "Your contributions", 0.0, 9600.0, 12648.13),
        ("15 Jan 2022", "Employer contributions", 0.0, 7200.0, 19848.13),
        ("30 Jun 2022", "Investment earnings", 0.0, -820.40, 19027.73),
        ("31 Dec 2022", "PIE tax at your PIR", 210.00, 0.0, 18817.73),
        ("31 Dec 2022", "Administration fees", 42.10, 0.0, 18775.63),
        ("15 Jan 2023", "Your contributions", 0.0, 9600.0, 28375.63),
        ("15 Jan 2023", "Employer contributions", 0.0, 7200.0, 35575.63),
        ("30 Jun 2023", "Investment earnings", 0.0, 2140.80, 37716.43),
        ("31 Dec 2023", "Administration fees", 58.20, 0.0, 37658.23),
        ("15 Jan 2024", "Your contributions", 0.0, 9600.0, 47258.23),
        ("15 Jan 2024", "Employer contributions", 0.0, 7200.0, 54458.23),
        ("30 Jun 2024", "Investment earnings", 0.0, 3510.60, 57968.83),
        ("31 Dec 2024", "Administration fees", 71.30, 0.0, 57897.53),
        ("15 Jan 2025", "Your contributions", 0.0, 9600.0, 67497.53),
        ("15 Jan 2025", "Employer contributions", 0.0, 7200.0, 74697.53),
        ("30 Jun 2025", "Investment earnings", 0.0, 4280.90, 78978.43),
        ("31 Dec 2025", "Administration fees", 84.60, 0.0, 78893.83),
        ("15 Jan 2026", "Your contributions", 0.0, 9600.0, 88493.83),
        ("15 Jan 2026", "Employer contributions", 0.0, 7200.0, 95693.83),
        ("30 Jun 2026", "Investment earnings", 0.0, 5120.30, 100814.13),
    ]
    df = pd.DataFrame(events, columns=["Date", "Transaction details", "debits", "Credits", "Balance"])
    # Scale debits/Credits, then recompute Balance as their cumulative sum — keeps the
    # ledger internally consistent (Balance must equal the running total of every
    # posting) rather than scaling the pre-computed Balance column separately.
    df["debits"] = df["debits"] * SCALE_KOWHAI
    df["Credits"] = df["Credits"] * SCALE_KOWHAI
    df["Balance"] = (df["Credits"] - df["debits"]).cumsum()
    df["debits"] = df["debits"].map(lambda v: f"-${v:,.2f}" if v else "")
    df["Credits"] = df["Credits"].map(lambda v: f"${v:,.2f}" if v else "")
    df["Balance"] = df["Balance"].map(lambda v: f"${v:,.2f}")
    df = df.iloc[::-1]  # newest first, matching the real export's ordering
    df.to_csv(EXPORTS_DIR / "Kowhai-transactions.csv", index=False)


# ---------------------------------------------------------------------------
# SouthernCross (AU super) — per-financial-year member-transaction CSVs, same shape
# as parse_southerncross.py expects.
# ---------------------------------------------------------------------------
def write_southerncross() -> None:
    rows = [
        {"Date": "2022-07-15", "Category": "CONTRIBUTIONS", "Title": "Employer - SG",
         "Total Amount": 5200.00},
        {"Date": "2022-07-15", "Category": "TAX", "Title": "Tax - Contributions",
         "Total Amount": -780.00},
        {"Date": "2022-10-15", "Category": "FEES", "Title": "Fee - Administration",
         "Total Amount": -95.00},
        {"Date": "2022-10-20", "Category": "FEES", "Title": "Tax benefit - Administration",
         "Total Amount": 28.50},
        {"Date": "2023-01-15", "Category": "CONTRIBUTIONS", "Title": "Employer - SG",
         "Total Amount": 5400.00},
        {"Date": "2023-01-15", "Category": "TAX", "Title": "Tax - Contributions",
         "Total Amount": -810.00},
        {"Date": "2023-03-01", "Category": "INVESTMENTS", "Title": "Investment earnings",
         "Total Amount": 28400.00},
        {"Date": "2023-06-30", "Category": "FEES", "Title": "Fee - Administration",
         "Total Amount": -410.00},
        {"Date": "2023-06-30", "Category": "FEES", "Title": "Tax benefit - Administration",
         "Total Amount": 123.00},
        {"Date": "2023-07-15", "Category": "CONTRIBUTIONS", "Title": "Employer - SG",
         "Total Amount": 22800.00},
        {"Date": "2023-07-15", "Category": "TAX", "Title": "Tax - Contributions",
         "Total Amount": -3420.00},
        # An internal switch into the fund's own self-managed option — no offsetting
        # amount anywhere, and not a real outflow. Excluded from the balance
        # reconstruction (see DIRECT_TRANSFER_TITLE in parse_southerncross.py).
        {"Date": "2023-09-08", "Category": "INVESTMENTS",
         "Title": "Investments - Member Direct transfer", "Total Amount": -18000.00},
        {"Date": "2024-01-15", "Category": "CONTRIBUTIONS", "Title": "Employer - SG",
         "Total Amount": 23500.00},
        {"Date": "2024-01-15", "Category": "TAX", "Title": "Tax - Contributions",
         "Total Amount": -3525.00},
        {"Date": "2024-03-01", "Category": "INVESTMENTS", "Title": "Investment earnings",
         "Total Amount": 61200.00},
        {"Date": "2024-06-30", "Category": "FEES", "Title": "Fee - Administration",
         "Total Amount": -680.00},
        {"Date": "2024-06-30", "Category": "FEES", "Title": "Tax benefit - Administration",
         "Total Amount": 204.00},
        {"Date": "2024-07-15", "Category": "CONTRIBUTIONS", "Title": "Employer - SG",
         "Total Amount": 24800.00},
        {"Date": "2024-07-15", "Category": "TAX", "Title": "Tax - Contributions",
         "Total Amount": -3720.00},
        {"Date": "2025-03-01", "Category": "INVESTMENTS", "Title": "Investment earnings",
         "Total Amount": 98600.00},
        {"Date": "2025-06-30", "Category": "FEES", "Title": "Fee - Administration",
         "Total Amount": -820.00},
        {"Date": "2025-06-30", "Category": "FEES", "Title": "Tax benefit - Administration",
         "Total Amount": 246.00},
        {"Date": "2025-07-15", "Category": "CONTRIBUTIONS", "Title": "Employer - SG",
         "Total Amount": 26100.00},
        {"Date": "2025-07-15", "Category": "TAX", "Title": "Tax - Contributions",
         "Total Amount": -3915.00},
        {"Date": "2026-03-01", "Category": "INVESTMENTS", "Title": "Investment earnings",
         "Total Amount": 142000.00},
        {"Date": "2026-06-30", "Category": "FEES", "Title": "Fee - Administration",
         "Total Amount": -960.00},
        {"Date": "2026-06-30", "Category": "FEES", "Title": "Tax benefit - Administration",
         "Total Amount": 288.00},
        {"Date": "2026-07-15", "Category": "CONTRIBUTIONS", "Title": "Employer - SG",
         "Total Amount": 27400.00},
        {"Date": "2026-07-15", "Category": "TAX", "Title": "Tax - Contributions",
         "Total Amount": -4110.00},
    ]
    df = pd.DataFrame(rows)
    df["Total Amount"] = df["Total Amount"] * SCALE_SOUTHERNCROSS
    # Split across financial-year files the same way the real export set arrives,
    # rather than one combined file — exercises the multi-file glob + concat path.
    # AU financial year ends 30 June: a date's own FY-end year is its calendar year if
    # it falls on or before 30 June, otherwise the following year.
    df["Date"] = pd.to_datetime(df["Date"])
    df["fy_end_year"] = df["Date"].dt.year + (df["Date"].dt.month > 6).astype(int)
    for fy_end_year, fy in df.groupby("fy_end_year"):
        fy = fy.drop(columns="fy_end_year").copy()
        fy["Date"] = fy["Date"].dt.date.astype(str)
        fy.to_csv(
            EXPORTS_DIR / f"SouthernCross.MemberTransactions.FY{fy_end_year}.csv", index=False
        )


def main() -> None:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_meridian()
    write_northbridge()
    write_crypto()
    write_kowhai()
    write_southerncross()
    print(f"Sample export files written to {EXPORTS_DIR}/")
    print("Now run: python pipeline/stage2_generate/run_dashboard.py")


if __name__ == "__main__":
    main()
