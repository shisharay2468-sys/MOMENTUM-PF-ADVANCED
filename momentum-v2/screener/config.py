"""All tunable parameters for the momentum system.

Edit this file to change the system's behaviour. Nothing else needs touching.
"""

# ---------------------------------------------------------------- universe
MIN_MARKET_CAP_CR = 1000.0      # rupees crore
MAX_MARKET_CAP_CR = 60000.0     # above this the momentum edge thins out and
                                # position sizes stop moving the needle
MIN_ADV_CR = 5.0                # 20-day average daily traded value, rupees crore
MIN_PRICE = 20.0                # rupees
MIN_HISTORY_DAYS = 300          # need a full 12m lookback plus buffer

# Main-board only. SME listings (NSE Emerge, BSE SME) have lot-size trading,
# thin books and 5% bands — momentum rules do not survive contact with them.
EXCLUDE_SME = True
ALLOWED_SERIES = ("EQ",)        # excludes SM, ST (SME), BE, BZ (trade-to-trade)

# ------------------------------------------------------- composite blocks
# The objective is a name that is STARTING a move, not one that has finished
# it. Four blocks, weighted. Must sum to 1.
W_TREND = 0.22          # is it trending at all, and smoothly
W_EMERGENCE = 0.38      # has it been coiling rather than running
W_FUNDAMENTALS = 0.25   # is the business accelerating underneath
W_VALUE = 0.15          # is there room in the multiple for a rerating

# Inside the emergence block
W_VOL_CONTRACTION = 0.30   # recent range tight against its own year
W_BASE = 0.30              # long time spent near the highs without running
W_QUIET_RUNUP = 0.25       # up modestly, not already extended
W_VOLUME_THRUST = 0.15     # volume waking up against its own average

# Inside the fundamentals block
W_EARNINGS_ACCEL = 0.45    # growth rate rising, not merely high
W_EARNINGS_LEVEL = 0.30
W_SALES_LEVEL = 0.25

# Small-company tilt. Multibaggers are far more common at the bottom of the
# cap range, so within your band, smaller gets a nudge.
W_SMALLCAP_TILT = 0.35

# ------------------------------------------------------------ momentum mix
# Weights inside the raw return blend. Must sum to 1.
W_R12_1 = 0.40                  # 12-month return, skipping the most recent month
W_R6 = 0.35
W_R3 = 0.25

# Composite: risk-adjusted momentum vs. trend-quality block
W_MOMENTUM_BLOCK = 0.60
W_QUALITY_BLOCK = 0.40

# Inside the trend-quality block
W_CONSISTENCY = 0.40            # share of positive months
W_ACCELERATION = 0.20           # 3m annualised beating 12m
W_PROXIMITY = 0.20              # closeness to 52-week high
W_REL_STRENGTH = 0.20           # RS line vs benchmark near its own high

# --------------------------------------------------------- entry criteria
# These apply ONLY to new buys. Existing holdings are never forced out for
# failing them — that is what the exit rules are for.
WEEKLY_RSI_MIN = 65.0           # 14-period RSI on weekly closes
WEEKLY_RSI_MAX = 80.0           # above this the move is overheated, not strong
MAX_EXT_20DMA = 0.12            # price no more than 12% above its 20-day avg
MAX_EXT_50DMA = 0.25            # and no more than 25% above its 50-day avg
MAX_EXT_ATR = 4.0              # and no more than 4 ATRs above the 20-day avg
USE_ATR_EXTENSION = False      # the two percentage caps above are enough

# Hard ceiling on how far a name has already run. A stock up more than this
# over the last year has had its move; buying it now is buying the tail of a
# distribution, not the middle. Set to None to disable.
MAX_1Y_RETURN = 1.50

# Relative strength against the mid-and-smallcap market. The ratio line must
# have made a fresh high recently — a stock can be rising and still be losing
# to its own peer group, and that is exactly what you do not want to own.
RS_HIGH_LOOKBACK = 50           # sessions the RS line must have topped
RS_HIGH_RECENT_DAYS = 30        # and it must have done so this recently

# ----------------------------------------------------------- new listings
# Recent IPOs cannot pass the main screen — they have no 12-month history —
# so they get their own list. A new listing qualifies only if it clears ALL
# of: the age test, the listing-day-high test, the technical tests and the
# growth tests below.
IPO_MAX_AGE_DAYS = 183          # listed within the last six months (calendar days)
IPO_MIN_DAYS = 10               # at least this many sessions of trading to judge
IPO_MIN_MARKET_CAP_CR = 1000.0
IPO_MAX_MARKET_CAP_CR = 60000.0
IPO_MIN_ADV_CR = 1.0            # 20-day average traded value, rupees crore

# Technical strength
IPO_REQUIRE_ABOVE_LISTING_HIGH = True   # close above the listing day's intraday high
IPO_REQUIRE_ABOVE_20DMA = True          # close above its 20-day average (10-day if younger)
IPO_MAX_FROM_HIGH = 0.15                # within 15% of its highest close since listing
IPO_REQUIRE_BEAT_MARKET = True          # up more than the mid/small market since listing

# Growth
IPO_MIN_SALES_GROWTH = 0.15     # sales growth, year on year
IPO_MIN_PROFIT_GROWTH = 0.0     # profit growth must be above this
# Return ratios are shown but not required by default: a fresh IPO has just
# raised equity, which drags ROE down for a year regardless of the business.
IPO_REQUIRE_RETURNS = False
IPO_MIN_ROE = 0.15
IPO_MIN_ROCE = 0.15
IPO_REQUIRE_TOP_SECTOR = False
IPO_TOP_SECTORS = 10

# ------------------------------------------------------ on-balance volume
# Monthly OBV, built exactly as a monthly chart builds it: each month's total
# volume is added if the month closed up, subtracted if it closed down. The
# signal is OBV crossing above its own 21-month EMA within the last two
# monthly bars (the current, still-forming month counts as one) and still
# being above it today.
OBV_EMA_SPAN = 21
OBV_CROSS_WITHIN_MONTHS = 2
OBV_REQUIRE_STILL_ABOVE = True
# The OBV list only shows names that also clear the main momentum gates.
# Set to False to see every liquid name in the cap band that crossed.
OBV_LIST_REQUIRES_GATES = True
# Set to True to make a fresh OBV cross a condition for every NEW buy in the
# book. Off by default because it shrinks the buyable list sharply.
OBV_REQUIRED_FOR_ENTRY = False

# Years of daily history to download. Five years gives about 60 monthly bars,
# enough for a properly formed 21-month EMA on OBV.
PRICE_HISTORY = "5y"

# ------------------------------------------------------------- signal log
# Every signal is written to state/signals.json with the date it first fired
# and never deleted. A signal that lapses and returns within this many days
# is treated as the same signal rather than a new one.
SIGNAL_REVIVE_DAYS = 5
SIGNAL_LOG_SHOW_DAYS = 365      # how far back the dashboard log goes

# Date-wise record: every trading day, the full list of stocks that passed
# each screen (momentum entry, OBV cross, IPO) is saved in state/daily.json.
# The file is never trimmed; the dashboard shows this many calendar days.
DAILY_SHOW_DAYS = 183           # six months

# ------------------------------------------------------ market-cap priority
# Companies below this market cap are given priority everywhere: they get a
# boost in the ranking that picks the book, and they are listed first in the
# OBV, IPO and date-wise lists. Names above it are still shown, flagged as
# lower priority.
PRIORITY_MCAP_CR = 50000.0      # rupees crore
PRIORITY_BONUS = 1.0            # z-score added to the composite (same scale
                                # as a hand-tagged catalyst, which is 1.2)

# ------------------------------------------------------------- catalysts
# A catalyst is the highest-priority input. Two sources feed it:
#   1. catalysts.csv — names you tag by hand (order wins, capacity, results)
#   2. an automatic episodic-pivot scan on price and volume
CATALYST_BONUS = 1.2            # z-score added for a hand-tagged catalyst
PIVOT_BONUS = 0.8               # z-score added for a detected episodic pivot
THEME_BONUS = 0.8               # z-score added for a sunrise-theme industry
CATALYST_MAX_AGE_DAYS = 120     # a tagged catalyst goes stale after this

# Episodic-pivot detection: a day of exceptional volume and range that the
# stock has since held onto. This is what an order-book announcement looks
# like on a chart.
PIVOT_LOOKBACK = 60             # sessions to scan
PIVOT_VOLUME_MULT = 3.0         # volume vs the 50-day average
PIVOT_MOVE = 0.07               # single-day move
PIVOT_MUST_HOLD = 0.92         # still holding 92% of the pivot day close

# ------------------------------------------------------------- trend gates
MAX_DIST_FROM_52W_HIGH = 0.25   # must trade within 25% of the 52-week high
SMA200_SLOPE_LOOKBACK = 20      # 200-DMA must be higher than N sessions ago

# Trend gates that can be switched off. Price above both moving averages is
# always required; these two extra confirmations are optional. Turning them
# off admits names whose long average has not yet turned up — earlier in a
# turnaround, and correspondingly less confirmed.
REQUIRE_GOLDEN_CROSS = False    # 50-day average above the 200-day
REQUIRE_SMA200_RISING = False   # 200-day average rising

# Fundamental checks. Each name must pass QUALITY_MIN_PASSES of those enabled.
USE_CASHFLOW_CHECK = False      # operating cash flow against reported profit
# Dropping a check without lowering this would TIGHTEN the screen: three of
# four is a higher bar than three of five. Two of four keeps the intent.
QUALITY_MIN_PASSES = 2

# ------------------------------------------------------------------ sector
TOP_SECTORS = 10                # only pick from the N strongest sectors
MAX_PER_SECTOR = 4
SECTOR_BONUS = 0.5              # z-score bonus for a top-3 sector with breadth
SECTOR_BONUS_BREADTH = 0.70     # share of sector above its 200-DMA
MIN_SECTOR_MEMBERS = 3          # sectors thinner than this are not ranked

# --------------------------------------------------------------- portfolio
PORTFOLIO_SIZE = 20
BUFFER_RANK = 35                # hold an existing name until it falls past this
MAX_TURNOVER = 8                # max replacements per quarterly rebalance
WEIGHTING = "equal"             # "equal" or "inverse_vol"
MIN_WEIGHT = 0.03
MAX_WEIGHT = 0.08
CASH_BUFFER = 0.05

# ------------------------------------------------------------- risk / exits
# Exits are checked every day and act immediately. They do not wait for the
# quarterly rebalance.
EXIT_BELOW_21WEMA = True        # weekly close below the 21-week EMA
INITIAL_STOP = 0.10             # 10% below entry price
EXIT_BELOW_SMA200 = True        # backstop for anything the above two miss
TRAILING_STOP = 0.0             # 0 disables; 0.25 = exit 25% off the high

# Refill vacancies as they happen rather than waiting for the quarter. With
# a 10% stop the book would otherwise bleed positions between rebalances.
REFILL_ON_EXIT = True
MAX_REFILLS_PER_RUN = 3

# ------------------------------------------------------------------ regime
BENCHMARK = "^CRSLDX"           # Nifty 500
BENCHMARK_FALLBACK = "NIFTYBEES.NS"   # used if the index has no history

# Relative strength is measured against the mid-and-smallcap market, not the
# broad index, because that is the pool these names actually compete in.
# Tried in order; if none has usable history the system builds an equal-weight
# proxy from the screening universe itself, which can never be unavailable.
RS_BENCHMARK_CANDIDATES = ("^NIFTYMIDSML400", "NIFTYMID150.NS", "^NSEMDCP50")
VIX = "^INDIAVIX"
VIX_PANIC = 25.0

# ---------------------------------------------------------------- fetching
BATCH_SIZE = 60                 # tickers per yfinance download call
META_CACHE_DAYS = 7             # re-pull sector / fundamentals weekly

# Metadata is one request per company, so a cold start would take hours and
# invite rate limiting. Instead each run pulls a slice and caches it. The
# system converges over the first three or four runs rather than failing on
# the first, and every run in between still produces a usable dashboard.
META_MAX_PER_RUN = 600
META_PAUSE_EVERY = 50           # short pause after this many, to stay polite
META_PAUSE_SECONDS = 1.5
FETCH_RETRIES = 3

# Quarterly results are a second request per company, so they are pulled only
# for the names that actually reach the dashboard rather than the whole
# market. That keeps the cost to about a hundred requests a run.
QUARTERLY_MAX = 100
QUARTERLY_CACHE_DAYS = 7
