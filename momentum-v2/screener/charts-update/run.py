"""Entry point. Run: python -m screener.run  [--offline-test] [--force-rebalance]"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

from . import config, data, portfolio, render, scoring, signals, charts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "index.html")


def _next_rebalance(today) -> str:
    ts = pd.Timestamp(today.date())
    for m in (1, 4, 7, 10):
        cand = pd.Timestamp(year=ts.year, month=m, day=1)
        if cand > ts:
            return cand.strftime("%-d %B %Y")
    return pd.Timestamp(year=ts.year + 1, month=1, day=1).strftime("%-d %B %Y")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline-test", action="store_true",
                    help="run the full pipeline on synthetic data")
    ap.add_argument("--force-rebalance", action="store_true")
    ap.add_argument("--force-warmup-rebalance", action="store_true",
                    help="build the book even while the universe is still loading")
    ap.add_argument("--limit", type=int, default=0,
                    help="cap the universe size (useful for a first run)")
    args = ap.parse_args(argv)

    today = data.today_ist()
    print(f"Momentum run — {today:%Y-%m-%d %H:%M} IST")
    state = data.load_state()
    holdings = state.get("holdings", {})

    if args.offline_test:
        from .synthetic import make_synthetic
        close, volume, meta, bench, vix = make_synthetic()
        high = close * 1.01
        universe_n = len(close.columns)
        pending = 0
        rs_bench = pd.Series(dtype=float)
    else:
        uni = data.load_universe()
        if args.limit:
            uni = uni.head(args.limit)
        tickers = uni["yf_ticker"].tolist()
        universe_n = len(tickers)
        print(f"Universe: {universe_n} NSE equities")

        print("Fetching metadata...")
        meta = data.fetch_meta(tickers, priority=list(holdings))
        pending = int(meta.attrs.get("pending", 0))
        # Trim on market cap before pulling prices — this is the single
        # biggest saving in runtime.
        mc = meta["market_cap_cr"].fillna(0)
        keep = meta[(mc >= config.MIN_MARKET_CAP_CR)
                    & (mc <= config.MAX_MARKET_CAP_CR)].index.tolist()
        # Always price what you own, even if it has drifted out of the band,
        # so its exit rules keep running.
        keep += [t for t in holdings if t not in keep]
        print(f"  {len(keep)} between Rs {config.MIN_MARKET_CAP_CR:,.0f} cr "
              f"and Rs {config.MAX_MARKET_CAP_CR:,.0f} cr")

        print("Fetching prices...")
        close, volume, high = data.fetch_prices(keep)
        bench = data.fetch_benchmark()
        rs_bench = data.fetch_rs_benchmark()
        vix = data.fetch_vix()

    print("Scoring...")
    catalysts = data.load_catalysts()
    themes = data.load_themes()
    if rs_bench is None or not len(rs_bench):
        rs_bench = data.build_midsmall_proxy(close)
        print("  relative strength measured against an equal-weight proxy "
              "built from the universe")
    metrics = scoring.compute_metrics(close, volume, meta, bench, rs_bench)
    metrics = scoring.catalyst_scores(metrics, catalysts, themes)
    gated = scoring.apply_gates(metrics)
    # Sector strength is measured across everything liquid and large enough.
    # Measuring it only on names that already passed the trend gates would
    # report 100% breadth for every sector, which tells you nothing.
    investable = gated[gated["g_mcap"] & gated["g_liquidity"]]
    sectors = scoring.sector_table(investable if len(investable) > 20 else gated)
    # Stage one: rank on everything available without extra network calls.
    prelim = scoring.composite(gated, sectors)

    # Stage two: pull quarterly results for the names that matter, feed the
    # earnings acceleration back in, and re-rank. Two passes cost one extra
    # in-memory sort and save fetching statements for the whole market.
    shortlist = list(prelim[prelim["eligible"]].sort_values(
        "composite", ascending=False).head(config.QUARTERLY_MAX).index)
    quarterly = {} if args.offline_test else data.fetch_quarterly(shortlist)

    for col, key in (("eps_accel", "eps_accel"), ("eps_yoy_q", "eps_yoy_q"),
                     ("eps_qoq", "eps_qoq"), ("sales_qoq", "sales_qoq")):
        gated[col] = pd.Series(
            {t: quarterly.get(t, {}).get(key) for t in gated.index}, dtype=float)

    scored = scoring.composite(gated, sectors)
    scored = scoring.sub_scores(scored, sectors)
    ipo_cands = scoring.new_listings(close, volume, meta, rs_bench, high)
    if ipo_cands:
        ipo_tickers = [c["ticker"] for c in ipo_cands]
        ipo_roce = {} if args.offline_test else data.fetch_roce(ipo_tickers)
        ipo_qtr = {} if args.offline_test else data.fetch_quarterly(ipo_tickers)
        ipos = scoring.filter_new_listings(ipo_cands, sectors, ipo_roce, ipo_qtr)
        print(f"  {len(ipo_cands)} recent listings above their listing-day high and "
              f"technically strong, "
              f"{len(ipos)} clear the quality tests")
    else:
        ipos = []
    eligible_n = int(scored["eligible"].sum())
    entry_n = int(scored["entry_ok"].sum())
    print(f"  {eligible_n} cleared the gates, {entry_n} are buyable today")

    def qtr(t: str, key: str):
        v = quarterly.get(t, {}).get(key)
        return float(v) if v is not None else None

    regime = portfolio.market_regime(bench, vix)
    print(f"  regime: {regime['state']}")

    # Do not build the opening book off a half-loaded universe. On a cold
    # start the metadata arrives over several runs, and a book chosen from the
    # first 600 names is not the best 20 in the market. Wait for full coverage.
    # The same applies to every later rebalance: ranking a partial market
    # would sell holdings simply because their data had not loaded yet.
    warming = bool(pending)
    if warming:
        print(f"  WARM-UP: {pending} companies still to load. "
              f"Holding off on any rebalance; exits still run.")

    due = (args.force_rebalance or
           portfolio.is_rebalance_due(today, state.get("last_rebalance")))
    if warming and not args.force_warmup_rebalance:
        due = False
    target = portfolio.build_target(scored, holdings, regime, due)
    dropped = list(target.attrs.get("dropped", [])) if due else []
    # A holding with no data today is never sold for that reason alone.
    no_data = [t for t in holdings if t not in scored.index]
    if no_data:
        print(f"  no data today for {len(no_data)} holding(s): "
              f"{', '.join(t.replace('.NS', '') for t in no_data)} — kept as held")
    dropped = [t for t in dropped if t not in no_data]

    # Daily exit checks run on whatever the book is, rebalance day or not.
    alerts, exit_now = portfolio.check_exits(target, holdings, close)
    if exit_now:
        target = target.drop(index=exit_now)
        dropped += exit_now
        fills = portfolio.refill(scored, list(target.index),
                                 regime["positions"] - len(target))
        if fills:
            add = scored.reindex(fills).copy()
            add["action"] = "buy"
            add["reason"] = [scored.loc[t, "catalyst_note"] or "Replaces an exited position"
                             for t in fills]
            target = pd.concat([target, add])
        target = portfolio._size_positions(target, regime)

    # ------------------------------------------------------------ payload
    book = []
    for t, r in target.iterrows():
        book.append({
            "ticker": t, "symbol": r["symbol"], "name": str(r["name"])[:38],
            "sector": r["sector"], "rank": int(r["rank"]) if pd.notna(r.get("rank")) else 0,
            "composite": float(r["composite"]) if pd.notna(r.get("composite")) else 0.0,
            "r12m": float(r["r12m"]), "r6m": float(r["r6m"]), "r3m": float(r["r3m"]),
            "ann_vol": float(r["ann_vol"]), "price": float(r["price"]),
            "quality_score": float(r["quality_score"]),
            "weekly_rsi": float(r["weekly_rsi"]) if pd.notna(r.get("weekly_rsi")) else None,
            "ext20": float(r["ext20"]) if pd.notna(r.get("ext20")) else None,
            "ema21w": float(r["ema21w"]) if pd.notna(r.get("ema21w")) else None,
            "rs_days": int(r["rs_days_since_high"]) if pd.notna(r.get("rs_days_since_high")) else None,
            "stop": float(holdings.get(t, {}).get("entry_price", r["price"])) * (1 - config.INITIAL_STOP),
            "catalyst": r.get("catalyst_note") or "",
            "eps_growth": float(r["earnings_growth"]) if pd.notna(r.get("earnings_growth")) else None,
            "sales_growth": float(r["revenue_growth"]) if pd.notna(r.get("revenue_growth")) else None,
            "eps_qoq": qtr(t, "eps_qoq"), "sales_qoq": qtr(t, "sales_qoq"),
            "quarter": quarterly.get(t, {}).get("quarter"),
            "emergence_score": float(r["emergence_score"]) if pd.notna(r.get("emergence_score")) else None,
            "eps_accel": float(r["eps_accel"]) if pd.notna(r.get("eps_accel")) else None,
            "emergence_score": float(r["emergence_score"]) if pd.notna(r.get("emergence_score")) else None,
         "eps_accel": float(r["eps_accel"]) if pd.notna(r.get("eps_accel")) else None,
         "sector_score": float(r["sector_score"]) if pd.notna(r.get("sector_score")) else None,
            "earnings_score": float(r["earnings_score"]) if pd.notna(r.get("earnings_score")) else None,
            "growth_score": float(r["growth_score"]) if pd.notna(r.get("growth_score")) else None,

            "obv_cross": bool(r.get("obv_cross")) if pd.notna(r.get("obv_cross")) else False,
            "obv_month": r.get("obv_cross_month") if isinstance(r.get("obv_cross_month"), str) else None,
            "weight": float(r["weight"]), "action": r["action"],
            "reason": r.get("reason", ""),
        })

    sells = []
    for t in dropped:
        row = scored.loc[t] if t in scored.index else None
        rank = int(row["rank"]) if row is not None and pd.notna(row.get("rank")) else None
        sym = row["symbol"] if row is not None else t.replace(".NS", "")
        hit = next((a for a in alerts if a["symbol"] == sym), None)
        why = (hit["kind"] if hit else
               (f"Rank {rank} — outside the {config.BUFFER_RANK} buffer"
                if rank else "No longer clears the gates"))
        sells.append({"symbol": sym, "reason": why})

    # Names that became buyable since the last run. This is the "entering
    # today" list — it updates daily, independent of the rebalance calendar,
    # so a fresh setup is visible the evening it appears.
    buyable_now = set(scored[scored["entry_ok"] & scored["g_sector"]].index)
    prev_buyable = set(state.get("buyable", []))
    fresh = [t for t in buyable_now - prev_buyable if t not in target.index]
    fresh_rows = scored.reindex(fresh).sort_values("composite", ascending=False)
    new_signals = [
        {"symbol": r["symbol"], "sector": r["sector"],
         "rank": int(r["rank"]) if pd.notna(r.get("rank")) else 0,
         "composite": float(r["composite"]) if pd.notna(r.get("composite")) else 0.0,
         "r12m": float(r["r12m"]),
         "weekly_rsi": float(r["weekly_rsi"]) if pd.notna(r.get("weekly_rsi")) else None,
         "ext20": float(r["ext20"]) if pd.notna(r.get("ext20")) else None,
         "rs_days": int(r["rs_days_since_high"]) if pd.notna(r.get("rs_days_since_high")) else None,
         "eps_growth": float(r["earnings_growth"]) if pd.notna(r.get("earnings_growth")) else None,
         "sales_growth": float(r["revenue_growth"]) if pd.notna(r.get("revenue_growth")) else None,
         "eps_qoq": qtr(_, "eps_qoq"), "sales_qoq": qtr(_, "sales_qoq"),
         "quarter": quarterly.get(_, {}).get("quarter"),
         "catalyst": r.get("catalyst_note") or ""}
        for _, r in fresh_rows.head(12).iterrows()
    ]
    state["buyable"] = sorted(buyable_now)

    held_or_target = set(target.index)
    pool = scored[scored["eligible"] & scored["g_sector"]].sort_values("composite", ascending=False)
    watch = [
        {"symbol": r["symbol"], "sector": r["sector"],
         "rank": int(r["rank"]), "composite": float(r["composite"]),
         "buyable": bool(r["entry_ok"]),
         "blocked": r.get("entry_blocked_by", ""),
         "catalyst": r.get("catalyst_note") or ""}
        for _, r in pool.iterrows() if _ not in held_or_target
    ][:10]

    sect_rows = [
        {"sector": s, "rank": int(r["rank"]), "breadth": float(r["breadth"]),
         "median_r6m": float(r["median_r6m"]), "members": int(r["members"])}
        for s, r in sectors.iterrows()
    ][:14]

    candidates = [
        {"symbol": r["symbol"], "name": str(r["name"])[:38], "sector": r["sector"],
         "rank": int(r["rank"]), "composite": float(r["composite"]),
         "r12m": float(r["r12m"]), "r6m": float(r["r6m"]), "r3m": float(r["r3m"]),
         "ann_vol": float(r["ann_vol"]), "price": float(r["price"]),
         "market_cap_cr": float(r["market_cap_cr"]),
         "weekly_rsi": float(r["weekly_rsi"]) if pd.notna(r.get("weekly_rsi")) else None,
         "ext20": float(r["ext20"]) if pd.notna(r.get("ext20")) else None,
         "ext50": float(r["ext50"]) if pd.notna(r.get("ext50")) else None,
         "rs_days": int(r["rs_days_since_high"]) if pd.notna(r.get("rs_days_since_high")) else None,
         "quality_score": float(r["quality_score"]),
         "buyable": bool(r["entry_ok"]),
         "blocked": r.get("entry_blocked_by", ""),
         "held": t in target.index,
         "eps_growth": float(r["earnings_growth"]) if pd.notna(r.get("earnings_growth")) else None,
         "sales_growth": float(r["revenue_growth"]) if pd.notna(r.get("revenue_growth")) else None,
         "eps_qoq": qtr(t, "eps_qoq"), "sales_qoq": qtr(t, "sales_qoq"),
         "quarter": quarterly.get(t, {}).get("quarter"),
         "emergence_score": float(r["emergence_score"]) if pd.notna(r.get("emergence_score")) else None,
         "eps_accel": float(r["eps_accel"]) if pd.notna(r.get("eps_accel")) else None,
         "sector_score": float(r["sector_score"]) if pd.notna(r.get("sector_score")) else None,
         "earnings_score": float(r["earnings_score"]) if pd.notna(r.get("earnings_score")) else None,
         "growth_score": float(r["growth_score"]) if pd.notna(r.get("growth_score")) else None,
         "obv_cross": bool(r.get("obv_cross")) if pd.notna(r.get("obv_cross")) else False,
         "obv_month": r.get("obv_cross_month") if isinstance(r.get("obv_cross_month"), str) else None,
         "catalyst": r.get("catalyst_note") or ""}
        for t, r in pool.head(60).iterrows()
    ]

    # ------------------------------------------------------------ OBV list
    base = (scored["eligible"] if config.OBV_LIST_REQUIRES_GATES
            else (scored["g_mcap"] & scored["g_liquidity"] & scored["g_price"]))
    obv_rows = scored[base & scored["obv_cross"].fillna(False).astype(bool)]
    obv_rows = obv_rows.assign(
        _pri=(obv_rows["market_cap_cr"] < config.PRIORITY_MCAP_CR).astype(int)
    ).sort_values(["_pri", "composite"], ascending=[False, False])
    obv_list = [
        {"symbol": r["symbol"], "name": str(r["name"])[:38], "sector": r["sector"],
         "rank": int(r["rank"]) if pd.notna(r.get("rank")) else 0,
         "composite": float(r["composite"]) if pd.notna(r.get("composite")) else 0.0,
         "price": float(r["price"]), "r12m": float(r["r12m"]),
         "r6m": float(r["r6m"]), "r3m": float(r["r3m"]),
         "ann_vol": float(r["ann_vol"]), "market_cap_cr": float(r["market_cap_cr"]),
         "weekly_rsi": float(r["weekly_rsi"]) if pd.notna(r.get("weekly_rsi")) else None,
         "ext20": float(r["ext20"]) if pd.notna(r.get("ext20")) else None,
         "rs_days": int(r["rs_days_since_high"]) if pd.notna(r.get("rs_days_since_high")) else None,
         "quality_score": float(r["quality_score"]),
         "buyable": bool(r["entry_ok"]), "blocked": r.get("entry_blocked_by", ""),
         "held": t in target.index,
         "obv_month": r.get("obv_cross_month"),
         "priority": bool(r["market_cap_cr"] < config.PRIORITY_MCAP_CR),
         "catalyst": f"OBV crossed its 21-month EMA in {r.get('obv_cross_month')}"}
        for t, r in obv_rows.iterrows()
    ]
    print(f"  {len(obv_list)} names with a fresh monthly OBV cross")

    # ------------------------------------------------------------ signal log
    stamp = today.strftime("%Y-%m-%d")
    entry_rows = scored.reindex(sorted(buyable_now))
    current = {
        "Entry": [{"symbol": r["symbol"], "name": str(r["name"])[:38],
                   "sector": r["sector"], "price": float(r["price"]),
                   "market_cap_cr": float(r["market_cap_cr"]) if pd.notna(r.get("market_cap_cr")) else None,
                   "rank": int(r["rank"]) if pd.notna(r.get("rank")) else None,
                   "detail": (f"Cleared every entry rule · rank "
                              f"{int(r['rank']) if pd.notna(r.get('rank')) else '--'}")}
                  for _, r in entry_rows.iterrows()],
        "OBV": [{"symbol": o["symbol"], "name": o["name"], "sector": o["sector"],
                 "price": o["price"], "market_cap_cr": o["market_cap_cr"], "rank": o["rank"],
                 "detail": f"Monthly OBV above its 21-month EMA, crossed {o['obv_month']}"}
                for o in obv_list],
        "IPO": [{"symbol": o["symbol"], "name": o["name"], "sector": o["sector"],
                 "price": o["price"], "market_cap_cr": o.get("market_cap_cr"),
                 "detail": (f"Listed {o['listed_date']} · listing-day high "
                            f"Rs {o['listing_high']:,.0f}")}
                for o in ipos],
    }
    sym_scored = set(scored["symbol"])
    evaluated = {"Entry": sym_scored, "OBV": sym_scored,
                 "IPO": {c.replace(".NS", "") for c in close.columns}}
    last_px = close.ffill().iloc[-1].dropna()
    prices = {t.replace(".NS", ""): float(v) for t, v in last_px.items()}
    log = [] if args.offline_test else signals.load()
    log, n_new_sig = signals.update(log, stamp, current, evaluated, prices)
    if not args.offline_test:
        signals.save(log)
    print(f"  signal log: {n_new_sig} new today, {len(log)} on record")

    # Date-wise record, keyed by the date of the closing prices, not the day
    # the workflow ran — a Sunday re-run files under Friday.
    price_day = pd.Timestamp(close.index[-1]).strftime("%Y-%m-%d") if len(close.index) else stamp
    daily = {} if args.offline_test else signals.load_daily()
    daily = signals.record_day(daily, price_day, current)
    if not args.offline_test:
        signals.save_daily(daily)
    daily_view = signals.daily_for_dashboard(daily, stamp, prices)
    print(f"  date-wise record: {len(daily)} trading days on file, "
          f"{len(daily_view)} shown")

    payload = {
        "stamp": today.strftime("%-d %B %Y"),
        "universe_n": universe_n,
        "eligible_n": eligible_n,
        "entry_n": entry_n,
        "regime": regime,
        "book": book,
        "sells": sells,
        "new_signals": new_signals,
        "first_run": not prev_buyable,
        "alerts": alerts,
        "sectors": sect_rows,
        "watchlist": watch,
        "candidates": candidates,
        "ipos": ipos,
        "obv": obv_list,
        "signal_log": signals.for_dashboard(log, stamp),
        "new_sig_today": n_new_sig,
        "daily": daily_view,
        "priority_mcap": config.PRIORITY_MCAP_CR,
        "top_sectors": config.TOP_SECTORS,
        "watch_from": (watch[0]["rank"] if watch else 0),
        "watch_to": (watch[-1]["rank"] if watch else 0),
        "weight_note": ("equal weight" if config.WEIGHTING == "equal"
                        else "inverse-volatility weighted"),
        "vacant": max(0, regime["positions"] - len(book)),
        "warming": warming,
        "pending": pending,
        "next_rebalance": _next_rebalance(today),
        "rebalanced": bool(due),
    }

    # Candlestick chart files for every stock on the page (display only).
    n_charts = charts.write(payload, close, volume, high, os.path.dirname(OUT),
                            data.CHART_OPEN, data.CHART_LOW)
    payload["charts"] = n_charts > 0
    print(f"  charts: {n_charts} stock charts written")
    render.render(payload, OUT)
    print(f"Dashboard written to {OUT}")

    if not args.offline_test:
        data.save_state(state)

    if (due or exit_now) and not args.offline_test:
        state["holdings"] = {
            t: {"entry_price": float(r["price"]),
                "entry_date": today.strftime("%Y-%m-%d"),
                "weight": float(r["weight"])}
            if r["action"] == "buy" else holdings.get(t, {"entry_price": float(r["price"])})
            for t, r in target.iterrows()
        }
        # Holdings with no data today were not in the target; keep them.
        for t in no_data:
            if t not in state["holdings"] and t not in exit_now:
                state["holdings"][t] = holdings[t]
        state["last_rebalance"] = today.strftime("%Y-%m-%d")
        state.setdefault("history", []).append({
            "date": today.strftime("%Y-%m-%d"),
            "bought": [b["symbol"] for b in book if b["action"] == "buy"],
            "sold": [s["symbol"] for s in sells],
        })
        data.save_state(state)
        print("State updated — rebalance recorded.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
