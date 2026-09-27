"""Candlestick chart data for every stock that appears on the dashboard.

Display only. Nothing here feeds the screen, the scores, or the book.

Each stock gets docs/charts/<SYMBOL>.json with up to five years of daily
open/high/low/close/volume. The dashboard loads a file only when you tap
"Chart", so the page itself stays small. Weekly and monthly candles, the
moving averages, and monthly OBV are all built in the browser from the daily
bars.

The chart files are rebuilt from scratch on every run and are NOT committed to
the repository (a .gitignore is written into docs/charts), so they never bloat
the repo's history. They reach the website through the workflow's
"Prepare dashboard for publishing" step, which publishes the docs folder as it
stands on the runner.
"""
from __future__ import annotations

import json
import os
import shutil

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lightweight-charts.js")
LIB_LICENSE = os.path.join(HERE, "LIGHTWEIGHT-CHARTS-LICENSE.txt")
YEARS = 5


def _symbols_in(payload: dict) -> set[str]:
    """Every symbol the dashboard can show, in any tab."""
    out: set[str] = set()

    def grab(rows):
        for r in rows or []:
            if isinstance(r, dict) and r.get("symbol"):
                out.add(str(r["symbol"]))

    for key in ("book", "sells", "candidates", "new_signals", "obv", "ipos",
                "signal_log", "alerts", "watch", "on_deck"):
        grab(payload.get(key))
    for day in payload.get("daily") or []:
        for kind, rows in day.items():
            if kind != "date":
                grab(rows)
    return out


def _col(frame, ticker):
    if frame is None or ticker not in getattr(frame, "columns", []):
        return None
    return frame[ticker]


def _series_json(ticker, close, volume, high, opn, low) -> dict | None:
    c = close[ticker].dropna()
    if len(c) < 5:
        return None
    start = c.index[-1] - pd.DateOffset(years=YEARS)
    c = c[c.index >= start]
    idx = c.index
    v = (_col(volume, ticker) if volume is not None else None)
    v = v.reindex(idx).fillna(0) if v is not None else pd.Series(0.0, index=idx)
    h = _col(high, ticker)
    o = _col(opn, ticker)
    lo = _col(low, ticker)
    h = h.reindex(idx) if h is not None else None
    o = o.reindex(idx) if o is not None else None
    lo = lo.reindex(idx) if lo is not None else None

    # Where a bar has no open (or the data source gave none), use the prior
    # close; highs and lows then at least bracket the open and close.
    prev = c.shift(1).fillna(c)
    o = o.fillna(prev) if o is not None else prev
    oc_hi = np.maximum(o, c)
    oc_lo = np.minimum(o, c)
    h = np.maximum(h.fillna(oc_hi), oc_hi) if h is not None else oc_hi
    lo = np.minimum(lo.fillna(oc_lo), oc_lo) if lo is not None else oc_lo

    def r(s):
        return [round(float(x), 2) for x in s]

    return {
        "t": [d.strftime("%Y-%m-%d") for d in idx],
        "o": r(o), "h": r(h), "l": r(lo), "c": r(c),
        "v": [int(x) for x in v.clip(lower=0)],
    }


def write(payload: dict, close: pd.DataFrame, volume: pd.DataFrame,
          high: pd.DataFrame | None, out_dir: str,
          opn: pd.DataFrame | None = None, low: pd.DataFrame | None = None) -> int:
    """Write one JSON per symbol into out_dir/charts. Returns files written.

    Never raises: a charting problem must not stop the screen from publishing.
    """
    try:
        cdir = os.path.join(out_dir, "charts")
        if os.path.isdir(cdir):
            shutil.rmtree(cdir)
        os.makedirs(cdir, exist_ok=True)
        # Keep the chart files out of git; they are published, not committed.
        with open(os.path.join(cdir, ".gitignore"), "w") as fh:
            fh.write("*\n")
        if os.path.exists(LIB):
            shutil.copyfile(LIB, os.path.join(cdir, "lightweight-charts.js"))
        if os.path.exists(LIB_LICENSE):
            shutil.copyfile(LIB_LICENSE, os.path.join(cdir, "LICENSE.txt"))

        written = 0
        for sym in sorted(_symbols_in(payload)):
            ticker = sym if sym in close.columns else f"{sym}.NS"
            if ticker not in close.columns:
                continue
            try:
                blob = _series_json(ticker, close, volume, high, opn, low)
            except Exception as exc:  # noqa: BLE001
                print(f"  chart for {sym} skipped ({exc})")
                continue
            if not blob:
                continue
            safe = "".join(ch for ch in sym if ch.isalnum() or ch in "-_&")
            with open(os.path.join(cdir, f"{safe}.json"), "w") as fh:
                json.dump(blob, fh, separators=(",", ":"))
            written += 1
        return written
    except Exception as exc:  # noqa: BLE001
        print(f"  WARNING: charts not written ({exc}); the dashboard still publishes")
        return 0
