"""
Basic Usage Examples for Market Truth Framework

Shows common usage patterns and best practices
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from market_truth.core.framework import MarketTruthFramework


def example_1_basic_analysis():
    """Example 1: Basic stock analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Analysis")
    print("="*80 + "\n")

    mtf = MarketTruthFramework()
    analysis = mtf.analyze('AAPL')

    # Access key results
    print(f"Ticker: {analysis['ticker']}")
    print(f"Conviction: {analysis['synthesis']['conviction']}")
    print(f"Action: {analysis['synthesis']['action']}")
    print(f"Score: {analysis['synthesis']['weighted_score']:.1f}/100")
    print(f"Reasoning: {analysis['synthesis']['reasoning']}")


def example_2_layer_by_layer():
    """Example 2: Examine each layer's results"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Layer-by-Layer Analysis")
    print("="*80 + "\n")

    mtf = MarketTruthFramework()
    analysis = mtf.analyze('MSFT')

    print(f"Analysis for {analysis['ticker']}:\n")

    for layer_name, layer_data in analysis['layers'].items():
        if isinstance(layer_data, dict):
            score = layer_data.get('score', 'N/A')
            print(f"  {layer_name.replace('_', ' ').title():30s} {score}/10")

            # Show red flags if any
            if 'red_flags' in layer_data and layer_data['red_flags']:
                print(f"    Red Flags: {', '.join(layer_data['red_flags'][:3])}")


def example_3_check_temporal_changes():
    """Example 3: Track changes over time"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Temporal Analysis")
    print("="*80 + "\n")

    mtf = MarketTruthFramework()

    # Run analysis twice to see temporal tracking
    print("First analysis (creates baseline):")
    analysis1 = mtf.analyze('NVDA')
    print(f"  Score: {analysis1['synthesis']['weighted_score']:.1f}")

    # Run again (in real usage, this would be days/weeks later)
    print("\nSecond analysis (compares to baseline):")
    analysis2 = mtf.analyze('NVDA')

    if analysis2.get('temporal'):
        temporal = analysis2['temporal']
        print(f"  Headline: {temporal['summary']['headline']}")
        print(f"  Recommendation: {temporal['summary']['recommendation']}")

        if temporal['summary'].get('key_changes'):
            print("\n  Key Changes:")
            for change in temporal['summary']['key_changes']:
                print(f"    - {change}")


def example_4_portfolio_screening():
    """Example 4: Analyze multiple stocks"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Portfolio Screening")
    print("="*80 + "\n")

    portfolio = ['AAPL', 'MSFT', 'GOOGL']
    mtf = MarketTruthFramework()

    results = []
    for ticker in portfolio:
        print(f"Analyzing {ticker}...")
        analysis = mtf.analyze(ticker)

        results.append({
            'ticker': ticker,
            'score': analysis['synthesis']['weighted_score'],
            'conviction': analysis['synthesis']['conviction'],
            'action': analysis['synthesis']['action']
        })

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    print("\nPortfolio Rankings:")
    print(f"{'Ticker':<10} {'Score':<10} {'Conviction':<15} {'Action':<15}")
    print("-" * 55)
    for r in results:
        print(f"{r['ticker']:<10} {r['score']:<10.1f} {r['conviction']:<15} {r['action']:<15}")


def example_5_filter_by_conviction():
    """Example 5: Filter stocks by conviction level"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Filter by Conviction")
    print("="*80 + "\n")

    tickers = ['AAPL', 'MSFT', 'NVDA', 'AMD', 'GOOGL']
    mtf = MarketTruthFramework()

    high_conviction = []
    for ticker in tickers:
        print(f"Screening {ticker}...")
        analysis = mtf.analyze(ticker)

        if analysis['synthesis']['conviction'] == 'HIGH':
            high_conviction.append({
                'ticker': ticker,
                'score': analysis['synthesis']['weighted_score'],
                'reasoning': analysis['synthesis']['reasoning']
            })

    print(f"\nHigh Conviction Stocks ({len(high_conviction)}):")
    for stock in high_conviction:
        print(f"\n  {stock['ticker']} - {stock['score']:.1f}/100")
        print(f"    {stock['reasoning']}")


def example_6_check_disqualifiers():
    """Example 6: Check for structural disqualifiers"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Check for Disqualifiers")
    print("="*80 + "\n")

    ticker = 'AAPL'
    mtf = MarketTruthFramework()
    analysis = mtf.analyze(ticker)

    synthesis = analysis['synthesis']

    print(f"Analyzing {ticker}:\n")
    print(f"  Disqualified: {synthesis.get('disqualified', False)}")

    if synthesis.get('disqualified'):
        print(f"\n  Reasons:")
        for rule in synthesis.get('override_rules', []):
            print(f"    - {rule}")
        print(f"\n  ⚠️  AVOID: Structural issues detected")
    else:
        print(f"\n  ✓ No structural disqualifiers found")


def example_7_access_raw_data():
    """Example 7: Access raw layer data for custom analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Access Raw Layer Data")
    print("="*80 + "\n")

    mtf = MarketTruthFramework()
    analysis = mtf.analyze('MSFT')

    # Access financial truth layer details
    if 'financial_truth' in analysis['layers']:
        fin = analysis['layers']['financial_truth']

        print("Financial Truth Details:")
        print(f"  Score: {fin.get('score')}/10")

        # Cash flow data
        if 'cash_flow' in fin and 'trends' in fin['cash_flow']:
            trends = fin['cash_flow']['trends']
            if 'ocf_change' in trends:
                print(f"  OCF Change: {trends['ocf_change']:.1f}%")

        # Debt analysis
        if 'debt' in fin and 'debt_profile' in fin['debt']:
            debt = fin['debt']['debt_profile']
            if debt.get('net_debt'):
                print(f"  Net Debt: ${debt['net_debt']/1e9:.2f}B")


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("MARKET TRUTH FRAMEWORK - USAGE EXAMPLES")
    print("="*80)

    examples = [
        ("Basic Analysis", example_1_basic_analysis),
        ("Layer-by-Layer", example_2_layer_by_layer),
        ("Temporal Changes", example_3_check_temporal_changes),
        ("Portfolio Screening", example_4_portfolio_screening),
        ("Filter by Conviction", example_5_filter_by_conviction),
        ("Check Disqualifiers", example_6_check_disqualifiers),
        ("Access Raw Data", example_7_access_raw_data),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nRun individual example:")
    print("  python examples/basic_usage.py <number>")
    print("\nRun all examples:")
    print("  python examples/basic_usage.py all")

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == 'all':
            for name, func in examples:
                func()
        else:
            try:
                idx = int(arg) - 1
                if 0 <= idx < len(examples):
                    examples[idx][1]()
                else:
                    print(f"Error: Example {arg} not found")
            except ValueError:
                print(f"Error: Invalid example number '{arg}'")
    else:
        # Default: run first example
        example_1_basic_analysis()


if __name__ == "__main__":
    main()
