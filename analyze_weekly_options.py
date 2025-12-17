"""
Weekly Options Analysis - Breakdown by week from start until Oct 8
"""

import csv
import re
from datetime import datetime, timedelta
from collections import defaultdict

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
    match = re.match(r'(\w+)\s+(\d{2}/\d{2}/\d{4})\s+(Call|Put)\s+\$?([\d.]+)', desc)
    if match:
        return {
            'ticker': match.group(1),
            'expiry': match.group(2),
            'type': match.group(3),
            'strike': float(match.group(4))
        }
    return None

def get_week_start(date):
    """Get the Monday of the week for a given date"""
    return date - timedelta(days=date.weekday())

def load_and_analyze():
    filename = r"c:\Users\batyr\OneDrive\Desktop\MyProjects\Trading\54fefe77-e0f2-5c6b-a5ed-af6b26184474.csv"

    trades = []

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

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

    for line in cleaned_lines[1:]:
        try:
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

    # Sort by date
    trades.sort(key=lambda x: x['date'])

    if not trades:
        print("No trades found!")
        return

    print("=" * 80)
    print("OPTIONS TRADING ANALYSIS - WEEKLY BREAKDOWN")
    print("=" * 80)

    # Get date range
    start_date = trades[0]['date']
    end_date = trades[-1]['date']
    print(f"\nData Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Total Trades: {len(trades)}")

    # Weekly breakdown
    weekly_stats = defaultdict(lambda: {
        'trades': 0,
        'pnl': 0,
        'calls': 0,
        'puts': 0,
        'call_pnl': 0,
        'put_pnl': 0,
        'tickers': defaultdict(float),
        'best_trade': None,
        'worst_trade': None
    })

    # Track positions for P&L calculation
    positions = defaultdict(list)
    completed_trades = []

    for trade in trades:
        week_start = get_week_start(trade['date'])
        week_key = week_start.strftime('%Y-%m-%d')

        weekly_stats[week_key]['trades'] += 1
        weekly_stats[week_key]['pnl'] += trade['amount']

        if trade['option_type'] == 'Call':
            weekly_stats[week_key]['calls'] += 1
            weekly_stats[week_key]['call_pnl'] += trade['amount']
        else:
            weekly_stats[week_key]['puts'] += 1
            weekly_stats[week_key]['put_pnl'] += trade['amount']

        weekly_stats[week_key]['tickers'][trade['ticker']] += trade['amount']

    # Print weekly breakdown
    print("\n" + "=" * 80)
    print("WEEKLY P&L BREAKDOWN")
    print("=" * 80)

    running_total = 0
    weeks_sorted = sorted(weekly_stats.keys())

    print(f"\n{'Week Starting':<15} {'Trades':<8} {'P&L':<12} {'Running':<12} {'Calls':<8} {'Puts':<8} {'Top Ticker':<10}")
    print("-" * 80)

    for week in weeks_sorted:
        stats = weekly_stats[week]
        running_total += stats['pnl']

        # Find top ticker for the week
        top_ticker = max(stats['tickers'].items(), key=lambda x: x[1])[0] if stats['tickers'] else 'N/A'
        top_ticker_pnl = stats['tickers'].get(top_ticker, 0)

        pnl_str = f"${stats['pnl']:,.0f}"
        running_str = f"${running_total:,.0f}"

        # Add color indicators
        pnl_indicator = "+" if stats['pnl'] >= 0 else ""

        print(f"{week:<15} {stats['trades']:<8} {pnl_indicator}{pnl_str:<11} {running_str:<12} {stats['calls']:<8} {stats['puts']:<8} {top_ticker:<10}")

    # Summary stats
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    total_pnl = sum(s['pnl'] for s in weekly_stats.values())
    total_trades = sum(s['trades'] for s in weekly_stats.values())
    total_calls = sum(s['calls'] for s in weekly_stats.values())
    total_puts = sum(s['puts'] for s in weekly_stats.values())
    call_pnl = sum(s['call_pnl'] for s in weekly_stats.values())
    put_pnl = sum(s['put_pnl'] for s in weekly_stats.values())

    winning_weeks = sum(1 for s in weekly_stats.values() if s['pnl'] > 0)
    total_weeks = len(weekly_stats)

    print(f"\nTotal P&L: ${total_pnl:,.2f}")
    print(f"Total Trades: {total_trades}")
    print(f"Total Weeks: {total_weeks}")
    print(f"Winning Weeks: {winning_weeks} ({100*winning_weeks/total_weeks:.1f}%)")
    print(f"\nCalls: {total_calls} trades, ${call_pnl:,.2f}")
    print(f"Puts: {total_puts} trades, ${put_pnl:,.2f}")

    # Top tickers overall
    print("\n" + "=" * 80)
    print("TOP TICKERS BY P&L")
    print("=" * 80)

    ticker_totals = defaultdict(lambda: {'pnl': 0, 'trades': 0})
    for trade in trades:
        ticker_totals[trade['ticker']]['pnl'] += trade['amount']
        ticker_totals[trade['ticker']]['trades'] += 1

    sorted_tickers = sorted(ticker_totals.items(), key=lambda x: x[1]['pnl'], reverse=True)

    print(f"\n{'Ticker':<10} {'Trades':<10} {'P&L':<15}")
    print("-" * 40)
    for ticker, stats in sorted_tickers[:15]:
        print(f"{ticker:<10} {stats['trades']:<10} ${stats['pnl']:,.2f}")

    # Worst tickers
    print("\n" + "=" * 80)
    print("WORST TICKERS BY P&L")
    print("=" * 80)
    print(f"\n{'Ticker':<10} {'Trades':<10} {'P&L':<15}")
    print("-" * 40)
    for ticker, stats in sorted_tickers[-10:]:
        print(f"{ticker:<10} {stats['trades']:<10} ${stats['pnl']:,.2f}")

    # Analysis by option price range
    print("\n" + "=" * 80)
    print("ANALYSIS BY OPTION PRICE RANGE")
    print("=" * 80)

    price_ranges = {
        '$0-1': (0, 1),
        '$1-3': (1, 3),
        '$3-6': (3, 6),
        '$6-10': (6, 10),
        '$10+': (10, 9999)
    }

    price_stats = defaultdict(lambda: {'trades': 0, 'pnl': 0})
    for trade in trades:
        if trade['trans'] == 'BTO':
            for range_name, (low, high) in price_ranges.items():
                if low <= trade['price'] < high:
                    price_stats[range_name]['trades'] += 1
                    price_stats[range_name]['pnl'] += trade['amount']
                    break

    print(f"\n{'Price Range':<12} {'Trades':<10} {'P&L':<15}")
    print("-" * 40)
    for range_name in ['$0-1', '$1-3', '$3-6', '$6-10', '$10+']:
        stats = price_stats[range_name]
        print(f"{range_name:<12} {stats['trades']:<10} ${stats['pnl']:,.2f}")

    # Weeks up to Oct 8 specifically
    print("\n" + "=" * 80)
    print("DETAILED WEEKLY BREAKDOWN (Up to Oct 8, 2025)")
    print("=" * 80)

    oct_8 = datetime(2025, 10, 8)

    print(f"\n{'Week':<15} {'Mon':<6} {'Tue':<6} {'Wed':<6} {'Thu':<6} {'Fri':<6} {'Weekly P&L':<12}")
    print("-" * 70)

    for week in weeks_sorted:
        week_date = datetime.strptime(week, '%Y-%m-%d')
        if week_date > oct_8:
            continue

        # Get daily breakdown for this week
        daily_pnl = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}  # Mon-Fri

        for trade in trades:
            trade_week = get_week_start(trade['date']).strftime('%Y-%m-%d')
            if trade_week == week:
                dow = trade['date'].weekday()
                if dow < 5:
                    daily_pnl[dow] += trade['amount']

        weekly_total = sum(daily_pnl.values())

        def fmt_pnl(v):
            if v == 0:
                return "-"
            return f"{v:+.0f}"

        print(f"{week:<15} {fmt_pnl(daily_pnl[0]):<6} {fmt_pnl(daily_pnl[1]):<6} {fmt_pnl(daily_pnl[2]):<6} {fmt_pnl(daily_pnl[3]):<6} {fmt_pnl(daily_pnl[4]):<6} ${weekly_total:,.0f}")

if __name__ == "__main__":
    load_and_analyze()
