"""Historical & current price enrichment: yfinance for stocks/FX/indexes *and* crypto
(the "XXX-USD" ticker format works for crypto directly, no separate dependency
needed), with a local cache so re-runs don't re-download years of history every time.

Caching contract: each series (one ticker's daily closes, one FX pair, one index) is
cached to data/cache/<key>.parquet. On each call, only dates after the cached max date
are fetched and appended — not the full history again. A cold cache still fetches the
full history once.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf
from config import BENCHMARK_TICKERS, ETF_SECTOR_LABEL, FX_TICKERS, KNOWN_ETFS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# yfinance logs its own "possibly delisted; no price data found" ERROR for every failed
# download — including narrow gap-fill windows that happen to land entirely on a
# weekend (no trading day exists to return). Harmless — _fetch() already catches this
# and the caller falls back to whatever's cached — but noisy on every run. We log our
# own warning when a fetch actually matters (see _fetch below); yfinance's duplicate
# ERROR is silenced here.
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(key: str) -> Path:
    safe = key.replace("^", "_").replace("=", "_").replace("/", "_")
    return CACHE_DIR / f"{safe}.parquet"


def _load_cache(key: str) -> pd.DataFrame | None:
    path = _cache_path(key)
    if path.exists():
        return pd.read_parquet(path)
    return None


def _save_cache(key: str, df: pd.DataFrame) -> None:
    df.to_parquet(_cache_path(key))


def get_historical_series(
    yf_ticker: str, start: date, cache_key: str | None = None
) -> pd.DataFrame:
    """Daily close prices for `yf_ticker` from `start` to today, cached incrementally.

    Returns a DataFrame with columns [date, close]. A failed/empty fetch returns
    whatever's cached (possibly empty) rather than raising — callers should treat an
    empty result as "unavailable" and degrade gracefully, not crash the whole run.
    """
    key = cache_key or yf_ticker
    cached = _load_cache(key)

    def _fetch(fetch_start: date, fetch_end: date) -> pd.DataFrame:
        try:
            raw = yf.download(
                yf_ticker,
                start=fetch_start.isoformat(),
                end=(fetch_end + timedelta(days=1)).isoformat(),
                progress=False,
                auto_adjust=True,  # split/dividend-adjusted closes
            )
        except Exception as e:  # noqa: BLE001 — degrade gracefully, never crash the run
            log.warning("price fetch failed for %s: %s", yf_ticker, e)
            return pd.DataFrame(columns=["date", "close"])
        if raw.empty:
            return pd.DataFrame(columns=["date", "close"])
        close_col = raw["Close"]
        if isinstance(close_col, pd.DataFrame):  # yfinance sometimes returns a 1-col frame
            close_col = close_col.iloc[:, 0]
        return pd.DataFrame({"date": close_col.index.date, "close": close_col.values})

    # Two independent gaps to fill, not one: cached data can be stale at the *end*
    # (needs today's close) and/or too short at the *start* (an earlier call asked for
    # a narrower window than this one). Checking only "is it fresh through today" and
    # ignoring how far back it goes would under-serve a wider request later.
    fresh_frames = [cached] if cached is not None and not cached.empty else []

    if cached is None or cached.empty:
        fresh_frames.append(_fetch(start, date.today()))
    else:
        earliest_cached = pd.to_datetime(cached["date"]).min().date()
        latest_cached = pd.to_datetime(cached["date"]).max().date()
        if start < earliest_cached:
            fresh_frames.append(_fetch(start, earliest_cached - timedelta(days=1)))
        if latest_cached < date.today():
            fresh_frames.append(_fetch(latest_cached + timedelta(days=1), date.today()))

    if not fresh_frames:
        return cached
    combined = pd.concat(fresh_frames, ignore_index=True)
    combined = combined.drop_duplicates(subset="date", keep="last").sort_values("date")
    if not combined.empty:
        _save_cache(key, combined)
    return combined if not combined.empty else (cached if cached is not None else combined)


def get_fx_series(currency: str, start: date) -> pd.DataFrame:
    """Historical AUD conversion rate for `currency` ('USD' or 'NZD').

    Returns [date, rate] where rate = <currency> per 1 AUD — divide a <currency> value
    by this to get AUD, for that same date (never use today's rate on a historical
    value).
    """
    if currency == "AUD":
        return pd.DataFrame({"date": [start], "rate": [1.0]})
    ticker = FX_TICKERS[currency]
    return get_historical_series(ticker, start, cache_key=f"fx_{currency}").rename(
        columns={"close": "rate"}
    )


def get_benchmark_series(start: date) -> dict[str, pd.DataFrame]:
    """Historical closes for the three benchmark indexes."""
    return {
        name: get_historical_series(ticker, start, cache_key=f"bench_{name}")
        for name, ticker in BENCHMARK_TICKERS.items()
    }


def get_sector(ticker: str) -> str:
    """GICS sector for a stock, "Crypto" for a crypto ticker, or ETF_SECTOR_LABEL for
    a fund/ETF.

    yfinance's `.info['sector']` returns nothing usable for ETFs — check quoteType
    first rather than assuming a clean sector string comes back. Crypto tickers
    (yfinance's "XXX-USD" format) are recognized directly rather than round-tripped
    through yfinance's info lookup — there's no sector to find there.
    """
    if ticker.endswith("-USD"):
        return "Crypto"
    if ticker in KNOWN_ETFS:
        return ETF_SECTOR_LABEL
    try:
        info = yf.Ticker(ticker).info
    except Exception as e:  # noqa: BLE001
        log.warning("sector lookup failed for %s: %s", ticker, e)
        return "Unclassified"
    quote_type = info.get("quoteType", "")
    if quote_type in ("ETF", "MUTUALFUND"):
        return ETF_SECTOR_LABEL
    return info.get("sector") or "Unclassified"


if __name__ == "__main__":
    # Smoke test against real public data — no personal holdings needed.
    start = date.today() - timedelta(days=14)

    print("-- AAPL (stock) --")
    print(get_historical_series("AAPL", start).tail(3))

    print("\n-- USD FX --")
    print(get_fx_series("USD", start).tail(3))

    print("\n-- Benchmarks --")
    for name, df in get_benchmark_series(start).items():
        print(name, "rows:", len(df))

    print("\n-- Sector: AAPL vs VTS.AX vs BTC-USD --")
    print("AAPL:", get_sector("AAPL"))
    print("VTS.AX:", get_sector("VTS.AX"))
    print("BTC-USD:", get_sector("BTC-USD"))

    print("\n-- Cache hit (should be instant, no network) --")
    print(get_historical_series("AAPL", start).tail(3))
