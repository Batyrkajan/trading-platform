# MULTI-DIRECTIONAL TRADING STRATEGY
## Options + Futures Framework
### December 14, 2025

---

## PART 1: YOUR DATA ANALYSIS RESULTS

### Overnight Options Strategy Performance

Based on analysis of 1,302 option trades:

| Metric | Value |
|--------|-------|
| **Total Overnight Trades** | 197 |
| **Win Rate** | 46.7% |
| **Total P&L** | +$14,408.88 |
| **Average Win** | +$344.74 |
| **Average Loss** | -$164.83 |
| **Risk/Reward Ratio** | 2.1:1 (favorable) |

### Overnight by Option Type

| Type | Count | Win Rate | P&L |
|------|-------|----------|-----|
| **CALLS** | 164 | 43.3% | +$10,258.64 |
| **PUTS** | 33 | 63.6% | +$4,150.24 |

**KEY INSIGHT**: Your overnight PUTS have a 63.6% win rate vs 43.3% for calls!

### Best Tickers for Overnight Strategy

| Ticker | Trades | Win Rate | P&L |
|--------|--------|----------|-----|
| ORCL | 10 | 70% | +$4,127 |
| AMD | 10 | 40% | +$3,115 |
| GS | 4 | 50% | +$2,058 |
| BABA | 12 | 58% | +$1,660 |
| AAPL | 15 | 60% | +$1,637 |
| MU | 7 | 43% | +$1,349 |
| TSM | 7 | 71% | +$1,064 |

### Day of Week Analysis

| Day | Trades | P&L | Signal |
|-----|--------|-----|--------|
| **Monday** | 261 | +$58,277 | BEST DAY |
| **Wednesday** | 160 | +$11,923 | 2nd Best |
| Tuesday | 382 | -$1,138 | Avoid |
| Thursday | 126 | -$1,194 | Avoid |
| **Friday** | 373 | -$4,308 | WORST |

---

## PART 2: BEARISH TRADING STRATEGY

### When to Play Bearish (PUTS)

```
BEARISH ENTRY CONDITIONS (Need 2+ of these):

┌─────────────────────────────────────────────────────────────┐
│ MARKET CONDITIONS                                           │
├─────────────────────────────────────────────────────────────┤
│ [ ] VIX rising AND above 20                                 │
│ [ ] QQQ/SPY below 20-day moving average                     │
│ [ ] Multiple red days in a row (3+)                         │
│ [ ] Major resistance rejection                               │
│ [ ] Negative news/catalyst (rate hike, weak earnings)        │
└─────────────────────────────────────────────────────────────┘

TECHNICAL CONFIRMATION:
├── Price closing below previous day's low
├── Increased selling volume
├── Breaking key support levels
└── RSI showing bearish divergence
```

### Your Proven Put Trades (Historical)

| Ticker | P&L | Notes |
|--------|-----|-------|
| AMD Puts | +$1,800 | Works well on tech selloffs |
| ORCL Puts | +$1,775 | Good on earnings plays |
| SPY Puts | +$1,303 | Portfolio hedge |
| GS Puts | +$483 | Financials hedge |

### Put Strike Selection

| Market Condition | Strike | Expiration |
|------------------|--------|------------|
| **Quick scalp** (1-2 days) | 2-3% OTM | Same week |
| **Swing trade** (3-7 days) | 5-7% OTM | 2 weeks out |
| **Portfolio hedge** | ATM or 3% OTM | 3-4 weeks out |
| **Black swan hedge** | 10-15% OTM | Monthly |

### Bearish Position Sizing

```
BEARISH TRADES ARE COUNTER-TREND = SMALLER SIZE

Account: $83,000
├── Max per bearish trade: 2% = $1,660
├── Portfolio hedge (SPY/QQQ puts): 3% = $2,490
└── Never more than 6% total in puts at once
```

---

## PART 3: OVERNIGHT OPTIONS STRATEGY (REFINED)

### Strategy: Buy EOD, Sell Next Morning

Based on your pattern of buying 1 hour before close, selling 30 min after open.

### Entry Rules (3:00-3:45 PM ET)

```
OVERNIGHT ENTRY CHECKLIST:

[ ] 1. TREND CHECK
    - If QQQ up on day → BUY CALLS
    - If QQQ down on day → BUY PUTS
    - If flat → SKIP (no edge)

[ ] 2. STOCK SELECTION
    - Use proven overnight tickers: ORCL, AMD, AAPL, TSM, BABA
    - Must have catalyst or be in clear trend

[ ] 3. STRIKE SELECTION
    - 2-4% OTM (closer than normal due to short hold)
    - Expiration: At least 1 week out (avoid 0DTE overnight)
    - Price: $1.00-$4.00 (sweet spot for overnight)

[ ] 4. TIMING
    - Buy between 3:00-3:45 PM ET
    - NOT in last 15 minutes (too volatile)

[ ] 5. SIZE
    - Max 2% per overnight trade ($1,660)
    - Can run 2-3 positions overnight = 4-6% total
```

### Exit Rules (9:30-10:00 AM ET)

```
MORNING EXIT STRATEGY:

AT OPEN (9:30 AM):
├── If gapping UP (calls) or DOWN (puts) > 3%:
│   └── SELL 50% immediately, trail rest
│
├── If flat or slight move your way:
│   └── Wait until 9:45-10:00 for better price
│
└── If gapping AGAINST you:
    └── SELL 100% immediately, cut loss

HARD RULES:
- Never hold past 10:30 AM
- If down >30% at open, EXIT
- If up >50% at open, TAKE PROFITS
```

### Overnight Risk Management

```
PRE-MARKET SCENARIOS:

Scenario A: +10% or more gap
├── Exit 75% at open
├── Trail 25% with tight stop
└── Expected: This happens ~20% of time

Scenario B: Flat to +10%
├── Wait for 9:45-10:00
├── Sell all by 10:00 AM
└── Expected: This happens ~50% of time

Scenario C: -10% to flat
├── Sell at open
├── Small loss, preserved capital
└── Expected: This happens ~25% of time

Scenario D: -10% or worse gap
├── SELL IMMEDIATELY at open
├── Do not hope for recovery
└── Expected: This happens ~5% of time
```

### Best Days for Overnight

Based on your data:
- **BUY Monday EOD, Sell Tuesday AM**: BEST
- **BUY Wednesday EOD, Sell Thursday AM**: Good
- **AVOID Friday overnight** (weekend gap risk)

---

## PART 4: MNQ FUTURES STRATEGY

### Position Sizing Analysis

```
YOUR PROPOSAL:
├── Account: $83,000
├── 2 MNQ contracts = ~$7,000 margin
├── Remaining buying power: $76,000
├── Margin utilization: 8.4%

VERDICT: CONSERVATIVE AND APPROPRIATE

MNQ SPECIFICATIONS:
├── Tick size: 0.25 points = $0.50 per contract
├── 1 point = $2 per contract
├── Daily range (typical): 150-300 points
├── 2 contracts max risk per day: $300-600 per 1% move
```

### MNQ Loss-Cutting Rules

```
HARD STOP-LOSS FRAMEWORK:

Per Trade Stop:
├── Max loss per trade: $200 per contract = $400 total
├── This equals 100 points on MNQ
├── Set HARD stop-loss order, not mental

Daily Stop:
├── Max daily loss: $600 (2 contracts)
├── If hit, DONE FOR THE DAY
├── Walk away, no revenge trading

Weekly Stop:
├── Max weekly loss: $1,500
├── If hit by Wednesday, no trading rest of week
├── Use time to review and learn
```

### MNQ Entry Rules

```
TREND IDENTIFICATION (Before Trading):

BULLISH Setup (Go LONG):
├── Price above VWAP
├── Higher highs, higher lows
├── QQQ futures green pre-market
└── No major resistance overhead

BEARISH Setup (Go SHORT):
├── Price below VWAP
├── Lower highs, lower lows
├── QQQ futures red pre-market
└── No major support nearby

NO TRADE (Chop/Range):
├── Price oscillating around VWAP
├── No clear direction
├── Mixed signals
└── STAY OUT - this killed your P&L
```

### MNQ Exit Rules

```
PROFIT TAKING:

Target 1: +50 points = +$100 per contract
├── Sell 1 contract
├── Move stop to breakeven on remaining

Target 2: +100 points = +$200 per contract
├── Trail stop 30 points behind
├── Let it run if trending

Target 3: +150+ points
├── Trail tight (20 points)
├── Take what market gives

STOP LOSS:

Initial Stop: -100 points = -$200 per contract
├── No exceptions
├── Set immediately after entry
├── If filled, accept the loss

Trailing Stop:
├── After +50 points: Move to breakeven
├── After +100 points: Trail 30 points behind
├── Never widen a stop
```

### MNQ Session Windows

```
BEST TIMES TO TRADE MNQ:

US PRE-MARKET (8:30-9:30 AM ET):
├── High volatility, news-driven
├── Good for momentum plays
├── Size down (1 contract only)

MARKET OPEN (9:30-11:00 AM ET):
├── Most volatile, most opportunity
├── Use 2 contracts max
├── Follow opening trend

MIDDAY (11:00 AM - 2:00 PM ET):
├── LOW VOLUME, CHOPPY
├── AVOID THIS PERIOD
├── This is where losses happen

AFTERNOON (2:00-4:00 PM ET):
├── Trend resumption often
├── Good for continuation plays
├── 2 contracts OK
```

---

## PART 5: COMBINED DAILY WORKFLOW

### Pre-Market (6:00-9:30 AM ET)

```
[ ] 1. Check overnight futures (MNQ, ES)
[ ] 2. Identify market direction (up/down/flat)
[ ] 3. Review any overnight options positions
[ ] 4. Check news on watchlist
[ ] 5. Set alerts for key levels
```

### Market Hours (9:30 AM - 4:00 PM ET)

```
MORNING SESSION (9:30-11:00):
├── Exit overnight options by 10:00
├── If trend clear, consider MNQ trades
├── Watch for breakout/breakdown

MIDDAY (11:00-2:00):
├── AVOID MNQ (choppy)
├── Research, plan afternoon trades
├── Monitor positions only

AFTERNOON (2:00-3:45):
├── MNQ trend trades if clear direction
├── 3:00-3:45: Set up overnight options
├── Follow overnight entry checklist
```

### End of Day (3:45-4:00 PM ET)

```
[ ] Close any MNQ positions (no overnight futures)
[ ] Confirm overnight option orders filled
[ ] Calculate daily P&L
[ ] Log trades
```

---

## PART 6: CAPITAL ALLOCATION

### Daily Capital Deployment

```
ACCOUNT: $83,000

ALLOCATION:

1. MNQ Futures Margin: $7,000 (8.4%)
   └── 2 contracts max
   └── Risk: $400/day max

2. Overnight Options: $5,000 (6%)
   └── 2-3 positions
   └── Risk: $1,500 max (if all fail)

3. Swing Options (if catalyst): $6,000 (7%)
   └── 1-2 positions
   └── From existing strategy

4. Cash Reserve: $65,000 (78%)
   └── Buying power for opportunities
   └── Safety cushion

DAILY MAX RISK: ~$2,500 (3% of account)
WEEKLY MAX RISK: ~$5,000 (6% of account)
```

---

## PART 7: DIRECTION DECISION FRAMEWORK

### How to Decide: Bullish, Bearish, or Neutral

```
MORNING CHECKLIST:

1. CHECK THE TREND (Most Important)

   UPTREND (Bullish):
   ├── QQQ above 5-day MA
   ├── VIX below 20 and falling
   ├── More green days than red (last 5)
   └── ACTION: Trade CALLS, go LONG MNQ

   DOWNTREND (Bearish):
   ├── QQQ below 5-day MA
   ├── VIX above 20 and rising
   ├── More red days than green (last 5)
   └── ACTION: Trade PUTS, go SHORT MNQ

   SIDEWAYS (Neutral):
   ├── QQQ oscillating around MA
   ├── VIX flat 15-20 range
   ├── Mixed signals
   └── ACTION: REDUCE SIZE or SKIP

2. CHECK THE CATALYST

   With Catalyst:
   ├── Trade the direction of catalyst
   ├── Full size (4% options, 2 MNQ)

   Without Catalyst:
   ├── Trade the trend only
   ├── Half size (2% options, 1 MNQ)
```

### Current Market Assessment (Dec 14, 2025)

```
MARKET STATUS: CAUTIOUS BEARISH SHORT-TERM

QQQ:
├── Down from recent highs
├── Last week: -1.9%
├── Near 20-day MA (watch for bounce or break)

VIX: 15.7
├── Normal range
├── Not panic, but not complacent

RECOMMENDED APPROACH FOR MONDAY:
├── NO OVERNIGHT Sunday night (weekend gap risk)
├── Watch first 30 minutes
├── If QQQ bounces, small CALL position
├── If QQQ breaks lower, PUTS or SHORT MNQ
├── SIZE DOWN until trend clarifies
```

---

## PART 8: TESTING FRAMEWORK

### Backtesting Your Strategies

To optimize results, track these metrics daily:

```
DAILY LOG:

Date: __________
Market Direction: UP / DOWN / FLAT

OVERNIGHT OPTIONS:
├── Ticker: _______ Call/Put
├── Entry Price: $_______
├── Exit Price: $_______
├── P&L: $_______
├── Notes: _______________________

MNQ FUTURES:
├── Direction: LONG / SHORT
├── Entry: _______ points
├── Exit: _______ points
├── Contracts: _______
├── P&L: $_______
├── Notes: _______________________

TOTAL P&L: $_______
```

### Weekly Review Metrics

```
WEEKLY SCORECARD:

Win Rate:
├── Overnight Options: ____%
├── MNQ Futures: ____%
├── Overall: ____%

P&L:
├── Overnight Options: $______
├── MNQ Futures: $______
├── Total: $______

Best Trade: ________________
Worst Trade: ________________
Lesson Learned: _____________
```

### Optimization Variables to Test

1. **Entry Time**: 3:00 vs 3:30 vs 3:45 PM
2. **Exit Time**: 9:35 vs 9:45 vs 10:00 AM
3. **Strike Distance**: 2% vs 3% vs 5% OTM
4. **MNQ Stop**: 75 vs 100 vs 125 points
5. **Day Selection**: Which days work best

---

## QUICK REFERENCE CARD

```
┌─────────────────────────────────────────────────────────────┐
│                  DAILY DECISION TREE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STEP 1: What's the trend?                                  │
│  ├── UP → Trade CALLS / LONG MNQ                           │
│  ├── DOWN → Trade PUTS / SHORT MNQ                         │
│  └── FLAT → SKIP or reduce size 50%                        │
│                                                             │
│  STEP 2: Is there a catalyst?                               │
│  ├── YES → Full size (4% options, 2 MNQ)                   │
│  └── NO → Half size (2% options, 1 MNQ)                    │
│                                                             │
│  STEP 3: Position sizing                                    │
│  ├── Overnight options: Max $1,660/trade, $5k total        │
│  ├── MNQ futures: 2 contracts, $400 stop                   │
│  └── Daily risk: Max $2,500                                │
│                                                             │
│  STEP 4: Execute and manage                                 │
│  ├── Options: Buy 3:00-3:45, Sell by 10:00 AM              │
│  ├── MNQ: Trade 9:30-11:00 and 2:00-4:00 only             │
│  └── HARD STOPS: Options -30%, MNQ 100 points              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## RULES TO NEVER BREAK

1. **Never hold MNQ overnight** - gap risk too high
2. **Always use hard stops** - no mental stops
3. **Daily loss limit $600 for futures** - walk away if hit
4. **Friday overnight = NO** - weekend gap risk
5. **Trade the trend, not your opinion** - data over ego
6. **Cut losses at -30% options, -100 pts MNQ** - no exceptions
7. **Size down when uncertain** - capital preservation first

---

*Framework created based on analysis of 1,302 options trades and futures data.*
*Key finding: Your overnight PUTS have 63.6% win rate - use this edge in downtrends.*
