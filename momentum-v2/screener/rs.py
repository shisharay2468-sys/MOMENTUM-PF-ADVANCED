"""RS rating, 1 to 99 — for the dashboard's filter only.

Nothing in the screen, the scores or the book reads this. It exists so you can
narrow any list on the dashboard to a relative-strength band (say 80-99).

Built the way IBD's RS rating is: a weighted 12-month price performance that
counts the latest quarter double,

    0.4 x 3-month  +  0.2 x 6-month  +  0.2 x 9-month  +  0.2 x 12-month

then ranked against every stock in the day's universe. 99 means the stock has
outperformed 99% of the market; 50 is the middle.

A stock with less than a year of history (a recent listing) is scored on the
periods it has: each missing period uses its return since listing. Under three
months of history gets no rating.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PERIODS = ((63, 0.4), (126, 0.2), (189, 0.2), (252, 0.2))
MIN_DAYS = 63


def ratings(close: pd.DataFrame) -> dict[str, int]:
    """Ticker -> RS rating 1..99. Never raises."""
    try:
        raw = {}
        for t in close.columns:
            s = close[t].dropna()
            if len(s) <= MIN_DAYS or s.iloc[-1] <= 0:
                continue
            last = float(s.iloc[-1])
            score = 0.0
            for days, w in PERIODS:
                base = float(s.iloc[-days - 1]) if len(s) > days else float(s.iloc[0])
                if base <= 0:
                    break
                score += w * (last / base - 1)
            else:
                raw[t] = score
        if not raw:
            return {}
        sr = pd.Series(raw)
        pct = sr.rank(pct=True, method="average")
        out = np.clip(np.ceil(pct * 99), 1, 99).astype(int)
        return {t: int(v) for t, v in out.items()}
    except Exception as exc:  # noqa: BLE001 — a display field must never stop a run
        print(f"  RS ratings skipped ({exc})")
        return {}


def attach(payload: dict, rating: dict[str, int]) -> None:
    """Write rs_rating onto every stock row the dashboard shows."""
    def look(sym):
        if sym is None:
            return None
        s = str(sym)
        return rating.get(s, rating.get(f"{s}.NS"))

    for key in ("book", "sells", "exits", "candidates", "new_signals", "obv",
                "ipos", "signal_log"):
        for r in payload.get(key) or []:
            if isinstance(r, dict) and r.get("symbol"):
                r["rs_rating"] = look(r["symbol"])
