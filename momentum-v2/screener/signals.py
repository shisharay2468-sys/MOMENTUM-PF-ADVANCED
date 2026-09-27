"""The signal log: every signal the system has ever raised, with its date.

Signals on the dashboard used to vanish the next evening. This file keeps
them. Each record notes the day it first fired and the price that day, and is
then kept up to date: whether it still qualifies, and the latest price, so
the dashboard can show what each signal has done since.

Stored in state/signals.json and committed back to the repository by the
daily workflow, so it survives between runs. Nothing is ever deleted.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

from . import config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "state", "signals.json")

TYPES = ("Entry", "OBV", "IPO")


def load(path: str = PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path) as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except Exception as exc:  # noqa: BLE001
        print(f"  WARNING: signal log unreadable ({exc}); starting a new one")
        return []


def save(log: list[dict], path: str = PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(log, fh, indent=1)
    os.replace(tmp, path)


def _days_between(a: str, b: str) -> int:
    return (datetime.strptime(b, "%Y-%m-%d") - datetime.strptime(a, "%Y-%m-%d")).days


def update(log: list[dict], today: str, current: dict[str, list[dict]],
           evaluated: dict[str, set], prices: dict[str, float]) -> tuple[list[dict], int]:
    """Merge today's signals into the log.

    current   -- {type: [ {symbol, name, sector, price, detail}, ... ]}
    evaluated -- {type: set of symbols the system actually looked at today}.
                 A signal is only marked ended if its symbol was evaluated
                 and failed. A name that simply had no data today (a failed
                 download, a half-loaded universe) keeps its signal alive.
    prices    -- latest close by symbol, to keep every record current.

    Returns (log, number of new signals added today).
    """
    added = 0
    for kind, items in current.items():
        live_now = {c["symbol"] for c in items}
        for c in items:
            sym = c["symbol"]
            recs = [r for r in log if r["type"] == kind and r["symbol"] == sym]
            active = next((r for r in recs if r.get("active")), None)
            if active is None:
                # A signal that blinked off for a day or two is the same signal.
                recent = [r for r in recs if r.get("ended")
                          and _days_between(r["ended"], today) <= config.SIGNAL_REVIVE_DAYS]
                if recent:
                    active = recent[-1]
                    active["active"] = True
                    active["ended"] = None
            if active is None:
                log.append({
                    "type": kind, "symbol": sym,
                    "name": c.get("name") or sym, "sector": c.get("sector") or "",
                    "date": today, "price": c.get("price"),
                    "detail": c.get("detail", ""),
                    "last_seen": today, "last_price": c.get("price"),
                    "active": True, "ended": None,
                })
                added += 1
            else:
                active["last_seen"] = today
                active["last_price"] = c.get("price", active.get("last_price"))

        for r in log:
            if (r["type"] == kind and r.get("active") and r["symbol"] not in live_now
                    and r["symbol"] in evaluated.get(kind, set())):
                r["active"] = False
                r["ended"] = today

    for r in log:
        p = prices.get(r["symbol"])
        if p:
            r["last_price"] = p
    return log, added


def for_dashboard(log: list[dict], today: str) -> list[dict]:
    """Recent records, newest first, with the move since each signal."""
    out = []
    for r in log:
        try:
            if _days_between(r["date"], today) > config.SIGNAL_LOG_SHOW_DAYS:
                continue
        except Exception:  # noqa: BLE001
            continue
        x = dict(r)
        p0, p1 = r.get("price"), r.get("last_price")
        x["since"] = (p1 / p0 - 1) if (p0 and p1) else None
        x["age"] = _days_between(r["date"], today)
        out.append(x)
    out.sort(key=lambda x: (x["date"], x["symbol"]), reverse=True)
    return out


# ------------------------------------------------------------ daily record
# A second, simpler store: for every trading day, the full list of stocks
# that passed each screen that day. The signal log above answers "when did
# this first fire"; this answers "what passed on 14 August". Stored in
# state/daily.json, keyed by the date of the closing prices used, so a
# re-run on the same day (or at the weekend) replaces that day rather than
# adding a duplicate. Nothing is ever deleted from the file; the dashboard
# shows the last DAILY_SHOW_DAYS.

DAILY_PATH = os.path.join(ROOT, "state", "daily.json")


def load_daily(path: str = DAILY_PATH) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # noqa: BLE001
        print(f"  WARNING: daily record unreadable ({exc}); starting a new one")
        return {}


def save_daily(daily: dict, path: str = DAILY_PATH) -> None:
    save(daily, path)


def _priority_key(x: dict):
    mc = x.get("mcap")
    pri = 0 if (mc is not None and mc < config.PRIORITY_MCAP_CR) else 1
    rk = x.get("rank") or 10_000
    return (pri, rk, x.get("symbol", ""))


def record_day(daily: dict, day: str, current: dict[str, list[dict]]) -> dict:
    """Store today's full pass lists under `day`, replacing any earlier run."""
    rec = {}
    for kind, items in current.items():
        rows = []
        for c in items:
            mc = c.get("market_cap_cr")
            rows.append({
                "symbol": c["symbol"],
                "name": (c.get("name") or c["symbol"])[:32],
                "sector": c.get("sector") or "",
                "price": round(float(c["price"]), 2) if c.get("price") else None,
                "mcap": round(float(mc)) if mc else None,
                "rank": c.get("rank"),
            })
        rows.sort(key=_priority_key)
        rec[kind] = rows
    daily[day] = rec
    return daily


def daily_for_dashboard(daily: dict, today: str, prices: dict[str, float]) -> list[dict]:
    """Days within DAILY_SHOW_DAYS, newest first, each stock with its move
    from that day's close to the latest close."""
    out = []
    for day in sorted(daily, reverse=True):
        try:
            if _days_between(day, today) > config.DAILY_SHOW_DAYS:
                continue
        except Exception:  # noqa: BLE001
            continue
        rec = {"date": day}
        for kind in TYPES:
            rows = []
            for r in daily[day].get(kind, []):
                x = dict(r)
                p0, p1 = r.get("price"), prices.get(r["symbol"])
                x["since"] = round(p1 / p0 - 1, 4) if (p0 and p1) else None
                x["pri"] = bool(r.get("mcap") is not None
                                and r["mcap"] < config.PRIORITY_MCAP_CR)
                rows.append(x)
            rec[kind] = rows
        out.append(rec)
    return out
