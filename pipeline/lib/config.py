"""Shared constants and classification rules for the net-worth pipeline.

Nothing here holds real data — holdings and balances live in data/exports/ (raw
export files, gitignored) and data/manual_holdings.yaml (hand-entered, committed).
"""

from __future__ import annotations

REPORTING_CURRENCY = "AUD"
DISPLAY_CURRENCIES = ("AUD", "NZD", "USD")

PLATFORMS = ("Meridian", "Northbridge", "Kowhai", "SouthernCross", "Crypto")

# Platforms whose balance can't be accessed on demand (locked until preservation age /
# retirement). Used for the liquid-vs-illiquid net worth split.
#
# Kowhai is NOT here despite being a KiwiSaver-style fund: it's actually two
# sub-accounts blended into one balance — a genuine KiwiSaver-locked portion and a
# larger freely-withdrawable portion. The raw export has no field separating the two,
# so the locked amount can't be tracked without a different export. Treat the whole
# platform as liquid rather than build tracking for an unreconstructable split — this
# overstates liquid net worth by the true locked amount, a documented approximation
# (see README's "Known limitations").
ILLIQUID_PLATFORMS = {"SouthernCross"}

# Platforms with no real export — tracked via data/manual_holdings.yaml instead of a
# parsed transaction/ledger history. No historical backfill is possible for these; they
# show as a step-series in the dashboard, not a daily reconstruction. Empty by default
# in this template — kept as live infrastructure for a genuinely manual-only asset
# (e.g. property) rather than deleted.
MANUAL_PLATFORMS: set[str] = set()

# yfinance tickers for the three benchmark indexes.
BENCHMARK_TICKERS = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
}

# Historical FX pairs needed to convert every holding's native currency to AUD for any
# date, not just today — required for the backfill, not just today's snapshot.
FX_TICKERS = {
    "USD": "AUDUSD=X",  # AUD per 1 USD needs inverting: value_usd / rate
    "NZD": "AUDNZD=X",  # AUD per 1 NZD needs inverting: value_nzd / rate
}

# asset_class is NOT inferred from ticker/exchange alone — an ASX-listed ticker isn't
# necessarily "AU equity" (e.g. a US-total-market ETF trading on the ASX). This table
# is checked first; anything not listed here falls back to a suffix-based default
# (see classify_asset_class below), which is only a reasonable guess, not a rule. Add
# an entry here for any holding where exposure and listing venue diverge.
ASSET_CLASS_OVERRIDES: dict[str, str] = {
    "VTS.AX": "US equity",  # Vanguard US Total Market Shares Index ETF — ASX-listed,
    # AUD-traded, but the fund's actual exposure is the US market, not Australia.
}

# GICS-style sector labels don't apply to funds/ETFs — yfinance's `.info['sector']`
# returns nothing usable for them. Anything with yfinance quoteType == "ETF" (or in
# this explicit list, as a fallback if quoteType lookup fails) gets this label instead
# of a forced/blank sector.
ETF_SECTOR_LABEL = "ETF / diversified"
KNOWN_ETFS = {"VTS.AX"}


def classify_asset_class(ticker: str, exchange_suffix_hint: str | None = None) -> str:
    """Classify a stock/ETF ticker's asset class by economic exposure.

    Checks the manual override table first (see ASSET_CLASS_OVERRIDES's docstring for
    why this can't be fully automated). Falls back to a suffix-based guess otherwise —
    correct most of the time, but flag any known exception in the override table above
    rather than trusting this blindly once real holdings are in.
    """
    if ticker in ASSET_CLASS_OVERRIDES:
        return ASSET_CLASS_OVERRIDES[ticker]
    if ticker.endswith("-USD"):  # yfinance's crypto ticker format, e.g. "BTC-USD"
        return "Crypto"
    if ticker.endswith(".AX") or ticker.endswith(".NZ"):
        return "AU equity" if ticker.endswith(".AX") else "NZ equity"
    return "US equity"
