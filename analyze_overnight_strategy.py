"""
Analyze overnight options strategy and bearish trades
- Buy before close, sell after open
- Analyze put vs call performance
- Identify patterns for optimal entry/exit
"""

import csv
import re
import sys
import io
from datetime import datetime, timedelta
from collections import defaultdict

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def parse_amount(amount_str):
    """Parse amount string to float"""
    if not amount_str:
        return 0
    amount_str = amount_str.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
    try:
        return float(amount_str)
    except:
        return 0

def parse_option_description(desc):
    """Parse option description to extract components"""
    # Format: "TICKER MM/DD/YYYY Call/Put $STRIKE"
    match = re.match(r'(\w+)\s+(\d{2}/\d{2}/\d{4})\s+(Call|Put)\s+\$?([\d.]+)', desc)
    if match:
        return {
            'ticker': match.group(1),
            'expiry': match.group(2),
            'type': match.group(3),
            'strike': float(match.group(4))
        }
    return None

def load_trades(filename):
    """Load and parse trades from CSV"""
    trades = []
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix multi-line entries
    lines = content.split('\n')
    cleaned_lines = []
    current_line = ""

    for line in lines:
        if not line.strip():
            continue
        if line.startswith('"') and ('BTO' in line or 'STC' in line or 'Activity Date' in line):
            if current_line:
                cleaned_lines.append(current_line)
            current_line = line
        else:
            current_line += " " + line.strip()
    if current_line:
        cleaned_lines.append(current_line)

    # Parse CSV
    for line in cleaned_lines[1:]:  # Skip header
        try:
            # Parse CSV fields
            fields = []
            in_quotes = False
            current_field = ""
            for char in line:
                if char == '"':
                    in_quotes = not in_quotes
                elif char == ',' and not in_quotes:
                    fields.append(current_field.strip())
                    current_field = ""
                else:
                    current_field += char
            fields.append(current_field.strip())

            if len(fields) >= 9:
                activity_date = fields[0]
                instrument = fields[3]
                description = fields[4]
                trans_code = fields[5]
                quantity = fields[6]
                price = fields[7]
                amount = fields[8]

                # Only process options (BTO/STC)
                if trans_code in ['BTO', 'STC']:
                    option_info = parse_option_description(description)
                    if option_info:
                        trades.append({
                            'date': datetime.strptime(activity_date, '%m/%d/%Y'),
                            'ticker': instrument,
                            'description': description,
                            'trans': trans_code,
                            'quantity': int(quantity) if quantity else 0,
                            'price': float(price.replace('$', '').replace(',', '')) if price else 0,
                            'amount': parse_amount(amount),
                            'option_type': option_info['type'],
                            'strike': option_info['strike'],
                            'expiry': option_info['expiry']
                        })
        except Exception as e:
            continue

    return trades

def analyze_overnight_trades(trades):
    """Analyze trades that were opened and closed on consecutive days"""
    print("\n" + "="*70)
    print("OVERNIGHT OPTIONS STRATEGY ANALYSIS")
    print("Buy before close Day N, Sell after open Day N+1")
    print("="*70)

    # Group trades by ticker and description
    positions = defaultdict(list)

    for trade in trades:
        key = (trade['ticker'], trade['description'])
        positions[key].append(trade)

    overnight_trades = []

    for key, pos_trades in positions.items():
        # Sort by date
        pos_trades.sort(key=lambda x: x['date'])

        # Find BTO/STC pairs
        buys = [t for t in pos_trades if t['trans'] == 'BTO']
        sells = [t for t in pos_trades if t['trans'] == 'STC']

        for buy in buys:
            for sell in sells:
                days_diff = (sell['date'] - buy['date']).days
                if 0 <= days_diff <= 2:  # Same day to 2 days later
                    pnl = sell['amount'] + buy['amount']  # buy is negative, sell is positive
                    pct_return = (sell['price'] / buy['price'] - 1) * 100 if buy['price'] > 0 else 0

                    overnight_trades.append({
                        'ticker': buy['ticker'],
                        'option_type': buy['option_type'],
                        'buy_date': buy['date'],
                        'sell_date': sell['date'],
                        'days_held': days_diff,
                        'buy_price': buy['price'],
                        'sell_price': sell['price'],
                        'quantity': min(buy['quantity'], sell['quantity']),
                        'pnl': pnl,
                        'pct_return': pct_return
                    })
                    break

    # Filter for overnight (1 day) trades
    true_overnight = [t for t in overnight_trades if t['days_held'] == 1]
    same_day = [t for t in overnight_trades if t['days_held'] == 0]
    two_day = [t for t in overnight_trades if t['days_held'] == 2]

    print(f"\n[TRADE DURATION BREAKDOWN]")
    print(f"   Same Day Trades: {len(same_day)}")
    print(f"   Overnight (1 day): {len(true_overnight)}")
    print(f"   2-Day Holds: {len(two_day)}")

    # Analyze overnight specifically
    if true_overnight:
        print(f"\n[OVERNIGHT TRADE ANALYSIS] (Buy Day N, Sell Day N+1):")
        print(f"   Total Overnight Trades: {len(true_overnight)}")

        winners = [t for t in true_overnight if t['pnl'] > 0]
        losers = [t for t in true_overnight if t['pnl'] <= 0]

        total_pnl = sum(t['pnl'] for t in true_overnight)
        avg_win = sum(t['pnl'] for t in winners) / len(winners) if winners else 0
        avg_loss = sum(t['pnl'] for t in losers) / len(losers) if losers else 0

        print(f"   Win Rate: {len(winners)}/{len(true_overnight)} ({100*len(winners)/len(true_overnight):.1f}%)")
        print(f"   Total P&L: ${total_pnl:,.2f}")
        print(f"   Avg Win: ${avg_win:,.2f}")
        print(f"   Avg Loss: ${avg_loss:,.2f}")

        # By option type
        calls = [t for t in true_overnight if t['option_type'] == 'Call']
        puts = [t for t in true_overnight if t['option_type'] == 'Put']

        print(f"\n   CALLS overnight:")
        if calls:
            call_winners = len([t for t in calls if t['pnl'] > 0])
            call_pnl = sum(t['pnl'] for t in calls)
            print(f"      Count: {len(calls)}, Win Rate: {100*call_winners/len(calls):.1f}%, P&L: ${call_pnl:,.2f}")

        print(f"   PUTS overnight:")
        if puts:
            put_winners = len([t for t in puts if t['pnl'] > 0])
            put_pnl = sum(t['pnl'] for t in puts)
            print(f"      Count: {len(puts)}, Win Rate: {100*put_winners/len(puts):.1f}%, P&L: ${put_pnl:,.2f}")

        # Top overnight trades
        print(f"\n   [TOP 10 OVERNIGHT WINNERS]")
        sorted_overnight = sorted(true_overnight, key=lambda x: x['pnl'], reverse=True)[:10]
        for t in sorted_overnight:
            print(f"      {t['ticker']} {t['option_type']}: ${t['buy_price']:.2f} → ${t['sell_price']:.2f} = ${t['pnl']:.2f} ({t['pct_return']:+.1f}%)")

        # By ticker
        print(f"\n   [OVERNIGHT BY TICKER]")
        ticker_stats = defaultdict(lambda: {'count': 0, 'wins': 0, 'pnl': 0})
        for t in true_overnight:
            ticker_stats[t['ticker']]['count'] += 1
            if t['pnl'] > 0:
                ticker_stats[t['ticker']]['wins'] += 1
            ticker_stats[t['ticker']]['pnl'] += t['pnl']

        for ticker, stats in sorted(ticker_stats.items(), key=lambda x: x[1]['pnl'], reverse=True)[:10]:
            wr = 100 * stats['wins'] / stats['count'] if stats['count'] > 0 else 0
            print(f"      {ticker}: {stats['count']} trades, {wr:.0f}% WR, ${stats['pnl']:,.2f}")

    return overnight_trades

def analyze_puts_vs_calls(trades):
    """Analyze put performance vs calls"""
    print("\n" + "="*70)
    print("PUTS VS CALLS ANALYSIS")
    print("="*70)

    calls = [t for t in trades if t['option_type'] == 'Call']
    puts = [t for t in trades if t['option_type'] == 'Put']

    print(f"\n[OVERALL BREAKDOWN]")
    print(f"   Call Trades: {len(calls)}")
    print(f"   Put Trades: {len(puts)}")

    # Calculate P&L by grouping BTO/STC
    def calc_pnl(trade_list):
        total = 0
        for t in trade_list:
            total += t['amount']
        return total

    call_pnl = calc_pnl(calls)
    put_pnl = calc_pnl(puts)

    print(f"\n   Call P&L: ${call_pnl:,.2f}")
    print(f"   Put P&L: ${put_pnl:,.2f}")

    # By ticker for puts
    print(f"\n[PUT TRADES BY TICKER]")
    put_by_ticker = defaultdict(list)
    for t in puts:
        put_by_ticker[t['ticker']].append(t)

    for ticker, ticker_trades in sorted(put_by_ticker.items(), key=lambda x: sum(t['amount'] for t in x[1]), reverse=True):
        pnl = sum(t['amount'] for t in ticker_trades)
        count = len(ticker_trades)
        print(f"   {ticker}: {count} trades, ${pnl:,.2f}")

def analyze_day_of_week(trades):
    """Analyze performance by day of week"""
    print("\n" + "="*70)
    print("DAY OF WEEK ANALYSIS")
    print("="*70)

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_stats = defaultdict(lambda: {'count': 0, 'amount': 0})

    for trade in trades:
        dow = trade['date'].weekday()
        if dow < 5:  # Weekday
            day_stats[days[dow]]['count'] += 1
            day_stats[days[dow]]['amount'] += trade['amount']

    print(f"\n[BY DAY OF WEEK]")
    for day in days:
        stats = day_stats[day]
        if stats['count'] > 0:
            print(f"   {day}: {stats['count']} trades, ${stats['amount']:,.2f}")

def main():
    filename = r"c:\Users\batyr\OneDrive\Desktop\MyProjects\Trading\54fefe77-e0f2-5c6b-a5ed-af6b26184474.csv"

    print("Loading trades...")
    trades = load_trades(filename)
    print(f"Loaded {len(trades)} option trades")

    # Run analyses
    analyze_puts_vs_calls(trades)
    overnight = analyze_overnight_trades(trades)
    analyze_day_of_week(trades)

    # Summary
    print("\n" + "="*70)
    print("KEY FINDINGS FOR OVERNIGHT STRATEGY")
    print("="*70)
    print("""
RECOMMENDATIONS BASED ON ANALYSIS:

1. OVERNIGHT STRATEGY (Buy EOD, Sell Next Morning):
   - Focus on tickers with historically positive overnight returns
   - Use this strategy primarily with CALLS when market trend is UP
   - Use this strategy with PUTS when market trend is DOWN

2. POSITION SIZING FOR OVERNIGHT:
   - Lower risk per trade (2% max) due to overnight gap risk
   - Set mental stop-loss at -30% for overnight holds

3. BEST DAYS TO ENTER:
   - Monday-Wednesday entries tend to work better
   - Avoid Friday entries (weekend risk)

4. BEARISH PLAYS:
   - Your put trades show [results above]
   - Consider QQQ/SPY puts for broader market hedging
""")

if __name__ == "__main__":
    main()
