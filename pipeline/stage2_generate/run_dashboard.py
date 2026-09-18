"""Builds outputs/dashboard.html from the pipeline modules.

Entry point — this is the one script you actually run (see README's "Try it in 60
seconds"). Lives in stage2_generate/ alongside nothing else on purpose: stage1_parse/
holds the five per-platform parsers this module calls, lib/ holds the shared modules
none of them run standalone. Both are siblings of this file's own parent (pipeline/),
not on Python's default import path when this file is run directly — the sys.path
bootstrap right below puts them there, then every import below it is a completely
ordinary flat import.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap: this file lives in pipeline/stage2_generate/, so Python only auto-adds
# that directory to sys.path — stage1_parse/ and lib/, its siblings under pipeline/,
# need adding explicitly before anything below can import from them. Every import
# after this block is a plain, unqualified one (import parse_meridian, from config
# import ..., etc.) — this is the only file in the whole pipeline that needs a
# bootstrap like this.
_PIPELINE_DIR = Path(__file__).resolve().parent.parent  # pipeline/
sys.path.insert(0, str(_PIPELINE_DIR / "lib"))
sys.path.insert(0, str(_PIPELINE_DIR / "stage1_parse"))

import json  # noqa: E402
from datetime import date, datetime, timedelta  # noqa: E402

import jinja2  # noqa: E402
import pandas as pd  # noqa: E402
import parse_crypto  # noqa: E402
import parse_kowhai  # noqa: E402
import parse_meridian  # noqa: E402
import parse_northbridge  # noqa: E402
import parse_southerncross  # noqa: E402
from aggregate import build_snapshot  # noqa: E402
from backfill import contributions_over_time, daily_grand_total, reconstruct_net_worth  # noqa: E402
from config import FX_TICKERS, ILLIQUID_PLATFORMS  # noqa: E402
from history import latest_manual_snapshot  # noqa: E402
from prices import get_benchmark_series, get_fx_series  # noqa: E402

TEMPLATE_DIR = _PIPELINE_DIR / "templates"
PROJECT_ROOT = _PIPELINE_DIR.parent  # repo root — outputs/ and data/ are its siblings
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "dashboard.html"
LAST_RUN_PATH = PROJECT_ROOT / "outputs" / "last_run.json"


def load_transactions():
    """Meridian + Northbridge + Crypto, all real transaction/ticker data. Kowhai and
    SouthernCross are NOT here — they're daily-balance ledgers, not transaction/ticker
    data, and are handled separately in build_dashboard_data().
    """
    return pd.concat(
        [parse_meridian.parse(), parse_northbridge.parse(), parse_crypto.parse()],
        ignore_index=True,
    ).sort_values("date")


def _clean_nans(obj):
    """Recursively replace float('nan') with None. Needed because pandas leaves NaN
    in place of missing values (e.g. `ticker` for a ledger fund, which has none) —
    json.dumps emits a literal `NaN` token for that, which isn't valid JSON.
    """
    if isinstance(obj, float) and obj != obj:  # NaN != NaN is the reliable check
        return None
    if isinstance(obj, dict):
        return {k: _clean_nans(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_nans(v) for v in obj]
    return obj


def series_to_dicts(df, value_col: str) -> list[dict]:
    return [{"date": d.isoformat(), "value": float(v)} for d, v in zip(df["date"], df[value_col])]


def build_transactions_by_ticker(transactions) -> dict:
    """Keyed on "platform:ticker", not ticker alone — the same ticker can exist on
    more than one platform as separate positions with separate histories; the
    drill-down needs to show the right one, not a merge of both.
    """
    out = {}
    for (platform, ticker), tx in transactions.groupby(["platform", "ticker"]):
        out[f"{platform}:{ticker}"] = [
            {
                "date": r["date"].isoformat(),
                "type": r["type"],
                "quantity": None if r["type"] == "dividend" else r["quantity"],
                "price": None if r["type"] == "dividend" else r["price"],
                "value": r["quantity"] if r["type"] == "dividend" else r["quantity"] * r["price"],
            }
            for _, r in tx.sort_values("date").iterrows()
        ]
    return out


def read_last_run() -> dict | None:
    if LAST_RUN_PATH.exists():
        return json.loads(LAST_RUN_PATH.read_text())
    return None


def write_last_run(total_net_worth: float) -> None:
    LAST_RUN_PATH.write_text(
        json.dumps({"date": date.today().isoformat(), "total_net_worth": total_net_worth})
    )


def _fees_to_aud(fees: pd.DataFrame) -> float:
    """Sum a [date, currency, amount] fee log to a single AUD total, converting each
    row at its own date's historical FX rate — same principle as every other
    historical conversion in this pipeline.
    """
    if fees.empty:
        return 0.0
    fx_cache: dict[str, pd.DataFrame] = {}

    def to_aud(row: pd.Series) -> float:
        if row["currency"] == "AUD":
            return row["amount"]
        if row["currency"] not in fx_cache:
            fx_cache[row["currency"]] = get_fx_series(row["currency"], fees["date"].min()).assign(
                date=lambda d: pd.to_datetime(d["date"]).dt.date
            )
        fx = fx_cache[row["currency"]]
        match = fx[fx["date"] == row["date"]]
        rate = match["rate"].iloc[0] if not match.empty else fx["rate"].iloc[-1]
        return row["amount"] / rate

    return float(fees.apply(to_aud, axis=1).sum())


def fees_paid_by_platform() -> dict[str, float]:
    """Lifetime fees paid per platform, AUD — Meridian/Northbridge brokerage fees
    (per-trade, converted at each trade's own date's FX rate) and Kowhai/SouthernCross
    administration fees (each platform's own total_fees_aud(), already AUD-converted).
    """
    return {
        "Meridian": _fees_to_aud(parse_meridian.load_fees()),
        "Northbridge": _fees_to_aud(parse_northbridge.load_fees()),
        "Kowhai": parse_kowhai.total_fees_aud(),
        "SouthernCross": parse_southerncross.total_fees_aud(),
    }


def current_fx_rates() -> dict[str, float]:
    """Today's (or most recently available) AUD-per-1 rate for each display currency —
    used by the dashboard's own currency toggle to convert AUD figures to NZD/USD for
    display. Real, live rates each run, not a hardcoded snapshot.
    """
    rates = {}
    for currency in FX_TICKERS:
        series = get_fx_series(currency, date.today() - timedelta(days=7))
        rates[currency] = float(series["rate"].iloc[-1]) if not series.empty else None
    return rates


def _xirr(cash_flows: list[tuple[date, float]]) -> float | None:
    """Money-weighted annualized rate of return (XIRR) via bisection on the net-present-
    value equation: find `rate` such that sum(cf / (1+rate)^years_since_first) == 0.

    `cash_flows` — negative for money going into the portfolio (each new contribution),
    positive for money coming out (here, just one: today's total net worth, as if
    cashed out) — must contain at least one of each sign, sorted by date. Approximates
    a sell as capital returned to the investor rather than reinvested, same
    simplification `contributions_over_time` already makes for the net-worth chart's
    contribution line.

    Pure-bisection, no scipy dependency: a portfolio's cash-flow sign pattern
    (all-negative contributions, then one final positive payout) has at most one
    positive-rate root by Descartes' rule of signs, so a simple search for where NPV
    crosses zero is enough.
    """
    if len(cash_flows) < 2:
        return None
    d0 = cash_flows[0][0]

    def npv(rate: float) -> float:
        return sum(cf / (1 + rate) ** ((d - d0).days / 365.0) for d, cf in cash_flows)

    f0 = npv(0.0)
    if f0 <= 0:  # net loss to date — no positive-rate answer, not attempting one
        return None
    lo, hi, f_lo = 0.0, 1.0, f0
    for _ in range(60):  # expand hi until NPV crosses zero, or give up
        if npv(hi) < 0:
            break
        hi *= 2
    else:
        return None
    for _ in range(200):  # bisect down to a precise root
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if f_lo * f_mid <= 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def _cash_flows_from_series(
    contrib_series: pd.Series, value_series: pd.Series
) -> list[tuple[date, float]]:
    """Builds _xirr()-ready cash flows from a cumulative-contributed series and a
    value series — shared by the portfolio-wide and per-platform annualized return
    figures below. Each real contribution/withdrawal day becomes one cash flow
    (negative in, positive out); the value series' own last entry becomes the final
    "as if cashed out today" flow.
    """
    if contrib_series.empty or value_series.empty:
        return []
    deltas = contrib_series.diff().fillna(contrib_series.iloc[0])
    flows = [(d, -float(delta)) for d, delta in deltas.items() if abs(delta) > 0.01]
    flows.append((value_series.index[-1], float(value_series.iloc[-1])))
    return flows


def _stock_platform_series(transactions, daily, platform: str) -> tuple[pd.Series, pd.Series]:
    """(value_series, contrib_series) for one Meridian/Northbridge/Crypto platform on
    its own — contributions_over_time()/daily_grand_total() normally operate on the
    combined transaction log, so this scopes both to a single platform first. Used
    only for the per-platform annualized return figure.
    """
    platform_tx = transactions[transactions["platform"] == platform]
    if platform_tx.empty:
        return pd.Series(dtype=float), pd.Series(dtype=float)
    contrib = contributions_over_time(platform_tx)
    contrib_series = (
        contrib.set_index("date")["contributed_aud"]
        if not contrib.empty
        else pd.Series(dtype=float)
    )
    value_df = daily_grand_total(daily[daily["platform"] == platform])
    value_series = (
        value_df.set_index("date")["value_aud"] if not value_df.empty else pd.Series(dtype=float)
    )
    return value_series, contrib_series


def _ledger_platform(name, platform, currency, module, full_date_range):
    """Computes (daily_series, contrib_series, holding_dict) for a real
    daily-balance-ledger platform — Kowhai and SouthernCross both work this way (a
    dollar ledger, not buy/sell/ticker data), just via different parsers and native
    currencies; this is the shared shape between them.
    """
    series = module.daily_aud_series(full_date_range)
    contrib_series = module.daily_contributed_aud_series(full_date_range)
    value_today = float(series.iloc[-1]) if len(series) else 0.0
    contrib_today = float(contrib_series.iloc[-1]) if len(contrib_series) else 0.0
    day_change = float(series.iloc[-1] - series.iloc[-2]) if len(series) >= 2 else 0.0
    holding = {
        "platform": platform,
        "name": name,
        "ticker": None,
        "value_aud": value_today,
        "cost_basis": contrib_today,
        "contributed_aud": contrib_today,
        "realized_gain": 0.0,
        "dividends_received": 0.0,
        "day_change_aud": day_change,
        "currency": currency,
        "asset_class": "Super",
        "sector": None,
        "liquid": platform not in ILLIQUID_PLATFORMS,
    }
    return series, contrib_series, holding


def build_dashboard_data() -> dict:
    transactions = load_transactions()
    manual_snapshot = latest_manual_snapshot()  # empty unless you add a manual asset

    daily = reconstruct_net_worth(transactions)  # Meridian + Northbridge + Crypto
    stock_daily_total = daily_grand_total(daily)

    kowhai_start = parse_kowhai.parse_daily_balance()["date"].min()
    southerncross_start = parse_southerncross.parse_daily_balance()["date"].min()
    stock_start = stock_daily_total["date"].min() if not stock_daily_total.empty else date.today()
    full_start = min(stock_start, kowhai_start, southerncross_start)
    full_date_range = list(pd.date_range(full_start, date.today(), freq="D").date)

    kowhai_series, kowhai_contrib_series, kowhai_holding = _ledger_platform(
        "Kowhai Growth Fund", "Kowhai", "NZD", parse_kowhai, full_date_range
    )
    southerncross_series, southerncross_contrib_series, southerncross_holding = _ledger_platform(
        "Southern Cross Super — Balanced",
        "SouthernCross",
        "AUD",
        parse_southerncross,
        full_date_range,
    )
    ledger_holdings = [kowhai_holding, southerncross_holding]

    # net worth: stocks/crypto (0 before their own start) + Kowhai's and
    # SouthernCross's real ledgers (0 before each one's own start) — all reindexed
    # onto the same full_date_range so they sum correctly day by day
    stock_series = (
        stock_daily_total.set_index("date")["value_aud"].reindex(full_date_range).fillna(0.0)
    )
    total_series = stock_series + kowhai_series + southerncross_series
    nw_series = [{"date": d.isoformat(), "value": float(v)} for d, v in total_series.items()]

    # contributions: stocks (real, from buy/sell) + Kowhai + SouthernCross (both real,
    # from their own ledgers' contribution rows)
    stock_contrib = contributions_over_time(transactions)
    stock_contrib_series = (
        stock_contrib.set_index("date")["contributed_aud"].reindex(full_date_range).fillna(0.0)
        if not stock_contrib.empty
        else pd.Series(0.0, index=pd.Index(full_date_range))
    )
    total_contrib_series = (
        stock_contrib_series + kowhai_contrib_series + southerncross_contrib_series
    )
    contrib_series = [
        {"date": d.isoformat(), "value": float(v)} for d, v in total_contrib_series.items()
    ]

    # Annualized (money-weighted) return, portfolio-wide and per-platform.
    annualized_return = _xirr(_cash_flows_from_series(total_contrib_series, total_series))
    annualized_by_platform = {}
    for platform in ("Meridian", "Northbridge", "Crypto"):
        platform_value, platform_contrib = _stock_platform_series(transactions, daily, platform)
        annualized_by_platform[platform] = _xirr(
            _cash_flows_from_series(platform_contrib, platform_value)
        )
    annualized_by_platform["Kowhai"] = _xirr(
        _cash_flows_from_series(kowhai_contrib_series, kowhai_series)
    )
    annualized_by_platform["SouthernCross"] = _xirr(
        _cash_flows_from_series(southerncross_contrib_series, southerncross_series)
    )

    # USD-basis re-expression of the net worth series: each day's AUD total multiplied
    # by that SAME day's own historical AUD/USD rate — not today's rate, which is all
    # the currency toggle elsewhere on the page does (a uniform scalar that can't
    # change the shape of the curve at all).
    fx_usd_hist = (
        get_fx_series("USD", full_start)
        .assign(date=lambda d: pd.to_datetime(d["date"]).dt.date)
        .set_index("date")["rate"]
        .reindex(full_date_range)
        .ffill()
        .bfill()
    )
    total_series_usd = total_series * fx_usd_hist
    total_contrib_series_usd = total_contrib_series * fx_usd_hist
    nw_series_usd = [
        {"date": d.isoformat(), "value": float(v)} for d, v in total_series_usd.items()
    ]
    contrib_series_usd = [
        {"date": d.isoformat(), "value": float(v)} for d, v in total_contrib_series_usd.items()
    ]

    snapshot = build_snapshot(transactions, manual_snapshot, daily, ledger_holdings)

    # Chart.js category-axis charts need every dataset on one chart to share the exact
    # same set of x labels. The portfolio series is daily; the raw index closes are
    # trading-days-only — reindex the indexes onto the portfolio's own daily range,
    # forward-filled across weekends/holidays, so both line up point-for-point.
    bench_range = list(stock_daily_total["date"]) if not stock_daily_total.empty else []
    bench = get_benchmark_series(stock_start) if not stock_daily_total.empty else {}

    def _bench_reindexed(label: str) -> list[dict]:
        if label not in bench or not bench_range:
            return []
        series = bench[label].set_index("date")["close"].reindex(bench_range).ffill().bfill()
        return [{"date": d.isoformat(), "value": float(v)} for d, v in series.items()]

    benchmark_series = {
        "portfolio": series_to_dicts(stock_daily_total, "value_aud"),
        "sp500": _bench_reindexed("S&P 500"),
        "nasdaq": _bench_reindexed("Nasdaq"),
        "dow": _bench_reindexed("Dow Jones"),
    }

    holdings = [
        {
            "name": h.get("name") or h.get("ticker"),
            "ticker": h["ticker"],
            "platform": h["platform"],
            "value": h["value_aud"],
            "cost": h.get("cost_basis"),
            "currency": h["currency"],
            "assetClass": h["asset_class"],
            "sector": h.get("sector"),
            "liquid": h["platform"] not in ILLIQUID_PLATFORMS,
            "dayChange": h.get("day_change_aud") or 0.0,
        }
        for h in snapshot["holdings"]
    ]

    manual_dates = {row["platform"]: row["date"] for row in manual_snapshot}

    def _platform_freshness(name: str, platform_key: str) -> dict:
        tx = transactions[transactions["platform"] == platform_key]
        if tx.empty:
            return {"name": name, "status": "stale", "text": "no export yet — see README"}
        return {
            "name": name,
            "status": "fresh",
            "text": f"data through {tx['date'].max().isoformat()}, {len(tx)} transactions",
        }

    def _ledger_freshness(name: str, module) -> dict:
        last_date = module.parse_daily_balance()["date"].max()
        return {
            "name": name,
            "status": "fresh",
            "text": f"ledger through {last_date.isoformat()}",
        }

    freshness = [
        _platform_freshness("Meridian", "Meridian"),
        _platform_freshness("Northbridge", "Northbridge"),
        _platform_freshness("Crypto", "Crypto"),
        _ledger_freshness("Kowhai", parse_kowhai),
        _ledger_freshness("SouthernCross", parse_southerncross),
    ]
    freshness += [
        {
            "name": platform,
            "status": "stale",
            "text": f"manual, entered {manual_dates[platform].isoformat()}"
            if platform in manual_dates
            else "no entry yet",
        }
        for platform in sorted({row["platform"] for row in manual_snapshot})
    ]

    last_run = read_last_run()
    since_last = (
        {
            "days": (date.today() - date.fromisoformat(last_run["date"])).days,
            "delta": snapshot["total_net_worth"] - last_run["total_net_worth"],
        }
        if last_run
        else {"days": None, "delta": None}
    )

    return {
        "holdings": holdings,
        "realizedByPlatform": snapshot["realized_by_platform"],
        "divMonthly": snapshot["monthly_dividends"],
        "sinceLastUpdate": since_last,
        "nwSeries": nw_series,
        "contribSeries": contrib_series,
        "nwSeriesUsd": nw_series_usd,
        "contribSeriesUsd": contrib_series_usd,
        "benchmarkSeries": benchmark_series,
        "transactionsByTicker": build_transactions_by_ticker(transactions),
        "freshness": freshness,
        "fxRates": current_fx_rates(),
        "annualizedReturn": annualized_return,
        "annualizedReturnByPlatform": annualized_by_platform,
        "feesPaid": fees_paid_by_platform(),
        "generatedAt": datetime.now().isoformat(timespec="minutes"),
        "isSampleData": True,
    }


def render(data: dict) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template("dashboard.html.j2")
    return template.render(data_json=json.dumps(_clean_nans(data)))


def main() -> None:
    data = build_dashboard_data()
    html = render(data)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html)
    total = sum(h["value"] or 0 for h in data["holdings"])
    write_last_run(total)
    print(f"Wrote {OUTPUT_PATH} ({len(html):,} bytes)")
    print(f"Total net worth: AUD {total:,.2f}\n")
    # Prices refresh live every run; transaction/balance data is only as fresh as the
    # last export you dropped into data/exports/ — this table is how you'd notice one
    # has gone stale.
    print("Freshness:")
    for f in data["freshness"]:
        print(f"  {f['name']:16} {f['text']}")
    stale = [f["name"] for f in data["freshness"] if f["status"] == "stale"]
    if stale:
        print(f"\nNOTE: still pending data: {', '.join(stale)} — see freshness row.")


if __name__ == "__main__":
    main()
