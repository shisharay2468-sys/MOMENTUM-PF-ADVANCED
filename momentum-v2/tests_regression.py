"""Full regression across every path the live system can take."""
import json, os, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screener import scoring, portfolio, data, render, config
from screener.synthetic import make_synthetic

fails = []
def check(name, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + name + ("  " + str(extra) if extra else ""))
    if not cond: fails.append(name)

close, volume, meta, bench, vix = make_synthetic()
proxy = data.build_midsmall_proxy(close)
check("proxy builds", len(proxy) == len(close) and proxy.iloc[-1] > 0)

m = scoring.compute_metrics(close, volume, meta, bench, proxy)
check("metrics computed", len(m) > 100, f"{len(m)} names")
check("no NaN in core cols", not m[["price","r12m","ann_vol","sma200","ema21w"]].isna().any().any())

m = scoring.catalyst_scores(m, {"SYN170": {"note": "Order win", "date": "2026-08-20"}}, {"power": 1.0})
check("catalyst applied", m.loc["SYN170.NS","catalyst_bonus"] >= config.CATALYST_BONUS)
check("theme applied", m[m.sector=="Power"]["catalyst_bonus"].min() >= config.THEME_BONUS)

g = scoring.apply_gates(m)
check("mcap band enforced",
      bool(((g[g.g_mcap].market_cap_cr >= config.MIN_MARKET_CAP_CR) &
            (g[g.g_mcap].market_cap_cr <= config.MAX_MARKET_CAP_CR)).all()))
check(f"RS gate at {config.RS_HIGH_RECENT_DAYS} days",
      bool((g[g.e_rs_high].rs_days_since_high <= config.RS_HIGH_RECENT_DAYS).all()),
      f"{int(g.e_rs_high.sum())} pass")
check("entry_ok implies eligible", bool((~g.entry_ok | g.eligible).all()))
check("blocked reasons populated", bool((g[~g.entry_ok & g.eligible].entry_blocked_by != "").all()))

sec = scoring.sector_table(g[g.g_mcap & g.g_liquidity])
check("sector breadth in range", bool(((sec.breadth >= 0) & (sec.breadth <= 1)).all()))
sc = scoring.composite(g, sec)
check("ranks unique", sc.dropna(subset=["rank"])["rank"].is_unique)

reg = portfolio.market_regime(bench, 13.0)
check("regime risk-on", reg["state"] == "risk-on")
check("regime unknown handles empty", portfolio.market_regime(pd.Series(dtype=float), None)["state"] == "unknown")
falling = bench * pd.Series(range(len(bench),0,-1), index=bench.index) / len(bench)
check("regime defensive on stress", portfolio.market_regime(falling, 31.0)["state"] == "defensive")

t0 = portfolio.build_target(sc, {}, reg, True)
check("opening book built", len(t0) > 0, f"{len(t0)} names")
check("sector cap honoured", int(t0.sector.value_counts().max()) <= config.MAX_PER_SECTOR)
check("weights sum sane", abs(t0.weight.sum() - (1-config.CASH_BUFFER)*reg["invested"]) < 1e-6)
check("all buys pass entry rules", bool(sc.loc[t0.index, "entry_ok"].all()))

pool = sc[sc.eligible & sc.g_sector].sort_values("composite", ascending=False)
h = {t: {"entry_price": float(sc.loc[t,"price"])*1.4} for t in pool.index[:10]}
t1 = portfolio.build_target(sc, h, reg, False)
check("non-rebalance holds only", set(t1.action.unique()) <= {"hold"})
al, ex = portfolio.check_exits(t1, h, close)
check("stops fire", len(ex) > 0, f"{len(ex)} exits")
check("exit reasons present", all(a.get("kind") and a.get("detail") for a in al))
rf = portfolio.refill(sc, list(t1.drop(index=ex).index), len(ex))
check("refill capped", len(rf) <= config.MAX_REFILLS_PER_RUN, f"{len(rf)}")
check("refills pass entry rules", bool(sc.loc[rf, "entry_ok"].all()) if rf else True)

check("OBV columns present", {"obv_cross","obv_above","obv_cross_month"} <= set(m.columns))
ipo_c = scoring.new_listings(close, volume, meta, proxy, close * 1.01)
check("IPO: strong listings found, faded one excluded",
      {c["symbol"] for c in ipo_c} >= {"IPO00"} and "IPO02" not in {c["symbol"] for c in ipo_c})
check("IPO: all above listing-day high", all(c["price"] > c["listing_high"] for c in ipo_c))
check("IPO: growth filter runs", isinstance(scoring.filter_new_listings(ipo_c, sec, {}, {}), list))
from screener import signals as sg
lg, n1 = sg.update([], "2026-09-01", {"OBV": [{"symbol": "X", "price": 10}]}, {"OBV": {"X"}}, {})
lg, n2 = sg.update(lg, "2026-09-02", {"OBV": [{"symbol": "X", "price": 11}]}, {"OBV": {"X"}}, {})
check("signal log keeps first date", n1 == 1 and n2 == 0 and lg[0]["date"] == "2026-09-01")
lg, _ = sg.update(lg, "2026-09-03", {"OBV": []}, {"OBV": {"X"}}, {})
check("lapsed signal is kept, marked ended", len(lg) == 1 and lg[0]["ended"] == "2026-09-03")

check("empty universe safe", len(portfolio.build_target(sc.head(0), {}, reg, True)) == 0)

st = data.load_state()
check("state loads", isinstance(st, dict) and "holdings" in st)
open("/tmp/bad.json","w").write("{corrupt")
import shutil; shutil.copy("/tmp/bad.json", os.path.join(data.STATE,"holdings.json"))
check("corrupt state recovers", data.load_state()["holdings"] == {})
open(os.path.join(data.STATE,"holdings.json"),"w").write(
    '{"holdings":{},"last_rebalance":null,"history":[],"buyable":[]}')

if not os.path.exists("docs/data.json"):
    # A brand-new repository has no dashboard yet; build one from synthetic data.
    from screener import run as _run
    _run.main(["--offline-test"])
for label, mut in [("normal", {}), ("warming", {"warming": True, "pending": 900}),
                   ("no book", {"book": [], "sells": [], "new_signals": [], "candidates": []})]:
    d = json.load(open("docs/data.json")); d.update(mut)
    p = render.render(d, f"/tmp/r_{label}/index.html")
    html = open(p).read()
    check(f"render {label}", len(html) > 15000 and "__" not in html.split("<script>")[0])

# ---- date-wise record and market-cap priority
from screener import signals as _sig
dd = {}
row = lambda s, mc: {"symbol": s, "name": s, "sector": "Power", "price": 100.0,
                     "market_cap_cr": mc, "rank": 5}
_sig.record_day(dd, "2026-03-01", {"Entry": [row("OLD", 5000)], "OBV": [], "IPO": []})
_sig.record_day(dd, "2026-09-25", {"Entry": [row("BIG", 55000), row("SMALL", 8000)],
                                   "OBV": [], "IPO": [row("NEWCO", 60000), row("TINY", 2000)]})
_sig.record_day(dd, "2026-09-25", {"Entry": [row("BIG", 55000), row("SMALL", 8000)],
                                   "OBV": [], "IPO": [row("NEWCO", 60000), row("TINY", 2000)]})
check("daily: same day re-run replaces, not duplicates", len(dd) == 2)
check("daily: under 50K cr listed first", [r["symbol"] for r in dd["2026-09-25"]["Entry"]] == ["SMALL", "BIG"])
check("daily: IPO column priority too", dd["2026-09-25"]["IPO"][0]["symbol"] == "TINY")
v = _sig.daily_for_dashboard(dd, "2026-09-27", {"SMALL": 110.0})
check("daily: older than six months hidden, not deleted", len(v) == 1 and "2026-03-01" in dd)
check("daily: move since that day", abs(v[0]["Entry"][0]["since"] - 0.10) < 1e-9)
pri = sc[sc.eligible].copy()
if len(pri) > 5:
    lo = pri.index[:1]
    m2 = g.copy(); m2.loc[lo, "market_cap_cr"] = 58000.0
    r_before = float(sc.loc[lo[0], "composite"])
    r_after = float(scoring.composite(m2, sec).loc[lo[0], "composite"])
    check("priority: 50K+ name loses the bonus", r_after < r_before)

print("\n" + ("ALL PASS" if not fails else f"{len(fails)} FAILED: {fails}"))
sys.exit(1 if fails else 0)
