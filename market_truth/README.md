# Market Truth Framework

**Domain 3: Balance Sheet & Cashflow Decay**

---

## 🎯 Purpose

Detect structural deterioration in companies weeks/months before the market realizes.

**Your edge:** Cash flow forensics and balance sheet analysis that reveals financial manipulation and business decay.

---

## 🏗️ The 7-Layer System

### Layer 1: Technical Entry
- When to pull the trigger
- From `screeners/technical_entry.py`

### Layer 2: Business Model Forensics
- Revenue quality (organic vs inorganic)
- Unit economics
- Moat strength
- Customer concentration

### Layer 3: Financial Truth ⭐ Core Edge
- Operating cash flow vs net income
- Receivables growth vs revenue
- Inventory dynamics
- Debt rollover stress
- Working capital deterioration

### Layer 4: Management Truth Detection
- Insider buying/selling patterns
- Compensation vs performance
- Communication analysis
- Board incentives

### Layer 5: Market Structure & Incentives
- Float analysis
- Short interest patterns
- Options positioning
- Institutional ownership

### Layer 6: Competitive Dynamics
- TAM reality check
- Competitor pressure
- Market share trends
- Pricing power

### Layer 7: Macro Forces
- Interest rate sensitivity
- Liquidity conditions
- Dollar impact
- Narrative cycle

### Layer 8: Synthesis (Intelligence Core)
- Cross-layer reasoning
- Industry-specific weighting
- Bayesian belief updates
- Conviction scoring

---

## 🚀 Usage

### Quick Analysis
```bash
python core/framework.py AAPL
```

### From Python
```python
from market_truth.core.framework import MarketTruthFramework

mtf = MarketTruthFramework()
analysis = mtf.analyze('AAPL')

print(f"Conviction: {analysis['synthesis']['conviction']}")
print(f"Action: {analysis['synthesis']['action']}")
print(f"Score: {analysis['synthesis']['weighted_score']}/100")
```

---

## 📊 Output Structure

```python
{
    'ticker': 'AAPL',
    'timestamp': datetime,
    'layers': {
        'business_model': {'score': 8, 'flags': [...]},
        'financial_truth': {'score': 7, 'flags': [...]},
        'management': {'score': 9, 'flags': [...]},
        # ... etc
    },
    'synthesis': {
        'conviction': 'HIGH',
        'action': 'BUY',
        'weighted_score': 82.5,
        'reasoning': '...',
        'key_risks': [...]
    }
}
```

---

## 📁 File Structure

```
market_truth/
├── core/
│   ├── framework.py            # Master orchestrator
│   ├── layer_schema.py         # Data structures
│   ├── synthesis_engine.py     # Cross-layer intelligence
│   └── temporal_engine.py      # Time-series tracking
│
├── analyzers/
│   ├── financial_truth.py      # Layer 3 ⭐ Core edge
│   ├── business_model.py       # Layer 2
│   ├── management_truth.py     # Layer 4
│   ├── market_structure.py     # Layer 5
│   ├── competitive_dynamics.py # Layer 6
│   ├── macro_forces.py         # Layer 7
│   └── risk_assessment.py      # Risk scoring
│
└── screeners/
    ├── truth_screener.py       # Universe scanner
    └── technical_entry.py      # Layer 1 (entry timing)
```

---

## 🎯 What It Detects

**Red Flags:**
- Receivables growing faster than revenue (fake sales)
- Inventory building without revenue growth (demand weakness)
- Gross margin compression (pricing power loss)
- Operating cash flow diverging from net income (quality issues)
- Debt rollover stress (liquidity crisis coming)
- Insider selling (management bailing)

**Green Flags:**
- Strong cash generation
- Revenue quality (organic growth)
- Competitive moat
- Aligned management incentives
- Favorable macro tailwinds

---

## 💰 Expected Performance

**Timeframe:** Weeks to months
**Frequency:** 2-5 trades per quarter
**Win Rate:** TBD (framework ready for validation)
**Position Duration:** 4-12 weeks
**Account Risk:** 5-10% per trade
**Capital Needed:** $10k-$25k

---

## 🔍 Example Analysis

```bash
$ python core/framework.py NVDA

================================================================================
MARKET TRUTH FRAMEWORK ANALYSIS: NVDA
================================================================================

Analyzing business model...
Extracting financial truth...
Detecting management truth...
Analyzing market structure...
Mapping competitive landscape...
Checking macro forces...
Assessing overall risk...

Running synthesis engine...

================================================================================
MARKET TRUTH ANALYSIS RESULTS: NVDA
================================================================================

LAYER SCORES (Raw):
  Business Model                 8/10 ↗ improving
  Financial Truth                6/10 ↘ deteriorating
  Management                     7/10 → stable
  Market Structure               9/10 ↗ improving
  Competitive                    8/10 → stable
  Macro                          7/10 ↗ improving
  Risk                           6/10 ↘ deteriorating

================================================================================
SYNTHESIS (Intelligence Core)
================================================================================
Raw Score:      51.0/70
Weighted Score: 73.5/100

Conviction:     MEDIUM
Action:         HOLD
Reasoning:      Strong business model and market position, but financial
                quality deteriorating. Receivables growing 50% faster than
                revenue. Wait for confirmation.

⚠️  STRUCTURAL DISQUALIFIERS:
  - Receivables/Revenue ratio > 1.5x (manipulation risk)
  - Gross margin compression > 3% (pricing pressure)

================================================================================
```

---

## 🛠️ API Architecture

### Centralized API Manager (v2.0)

All API access coordinated through single `APIManager` class:

**Features:**
- ✅ Automatic fallback (FMP → yfinance)
- ✅ Per-API rate limiting (no bans)
- ✅ Data quality tracking
- ✅ Error handling throughout
- ✅ SEC EDGAR integration

**Data Sources:**
- **Primary:** FMP API (currently deprecated endpoints, using yfinance)
- **Fallback:** Yahoo Finance (always available)
- **SEC Data:** SEC EDGAR filings (10-K, proxy, insider trades)

**Rate Limits:**
- FMP: 0.2s delay (5 req/s)
- SEC: 0.15s delay (~6 req/s)
- yfinance: 0.5s delay

### Configuration

Create `.env` in project root:
```bash
# Optional: SEC user identification
SEC_USER_EMAIL=your.email@example.com

# Optional: FMP API key (legacy endpoints deprecated)
FMP_API_KEY=your_key
```

### Test API Manager

```bash
python core/api_manager.py AAPL
```

---

## ✅ Status

**Framework:** ✅ Complete (v2.0)
**API Integration:** ✅ Complete (centralized manager with fallback)
**Rate Limiting:** ✅ Complete (per-API coordinated limits)
**Error Handling:** ✅ Complete (graceful degradation)
**Testing:** ✅ Complete (AAPL, NVDA, MSFT verified)
**Documentation:** ✅ Complete (README + API_FIXES_COMPLETE.md)

**Validation:** Track predictions vs actual outcomes (next step)

---

## 🚀 Next Steps

1. Run analysis on 10-20 stocks
2. Track predictions vs reality over 4-8 weeks
3. Refine scoring weights based on results
4. Identify which layers have strongest predictive power
5. Build conviction in the system

---

**This is Domain 3 of your shadow builder system.**

Shadow builders extract edge from market inefficiencies without attention or marketing.
