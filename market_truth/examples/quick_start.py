#!/usr/bin/env python3
"""
Quick Start Script for Market Truth Framework

Run this to verify everything is working correctly
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n[1/3] Checking dependencies...")

    required = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
        ('yfinance', 'yfinance'),
        ('dotenv', 'python-dotenv'),
        ('bs4', 'beautifulsoup4'),
    ]

    missing = []
    for module, package in required:
        try:
            __import__(module)
            print(f"  [+] {package}")
        except ImportError:
            print(f"  [x] {package} - MISSING")
            missing.append(package)

    if missing:
        print(f"\n[!] Missing dependencies:")
        print(f"    pip install {' '.join(missing)}")
        return False

    print("\n  [+] All dependencies installed")
    return True


def check_api_manager():
    """Test API manager initialization"""
    print("\n[2/3] Testing API manager...")

    try:
        from market_truth.core.api_manager import get_api_manager

        manager = get_api_manager()
        status = manager.get_api_status()

        print(f"  API Status:")
        for api, available in status.items():
            icon = "+" if available else "x"
            print(f"    [{icon}] {api}: {available}")

        if status.get('yfinance_available'):
            print("\n  [+] API manager working")
            return True
        else:
            print("\n  [!] yfinance not available (required)")
            return False

    except Exception as e:
        print(f"\n  [!] API manager error: {e}")
        return False


def run_sample_analysis():
    """Run a quick sample analysis"""
    print("\n[3/3] Running sample analysis...")

    try:
        from market_truth.core.framework import MarketTruthFramework

        print(f"\n  Analyzing AAPL (this may take 30-60 seconds)...")
        mtf = MarketTruthFramework()
        analysis = mtf.analyze('AAPL')

        print(f"\n  Results:")
        print(f"    Ticker: {analysis['ticker']}")
        print(f"    Score: {analysis['synthesis']['weighted_score']:.1f}/100")
        print(f"    Conviction: {analysis['synthesis']['conviction']}")
        print(f"    Action: {analysis['synthesis']['action']}")

        print(f"\n  Layer Scores:")
        for layer_name, layer_data in analysis['layers'].items():
            if isinstance(layer_data, dict):
                score = layer_data.get('score', 'N/A')
                print(f"    {layer_name.replace('_', ' ').title():30s} {score}/10")

        print("\n  [+] Framework working correctly!")
        return True

    except Exception as e:
        print(f"\n  [!] Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all checks"""
    print("\n" + "="*80)
    print("MARKET TRUTH FRAMEWORK - QUICK START")
    print("="*80)

    checks = [
        check_dependencies(),
        check_api_manager(),
        run_sample_analysis(),
    ]

    print("\n" + "="*80)
    if all(checks):
        print("[SUCCESS] Market Truth Framework is ready to use!")
        print("="*80)
        print("\nNext steps:")
        print("  1. Analyze a stock:")
        print("     python core/framework.py TICKER")
        print("\n  2. See examples:")
        print("     python examples/basic_usage.py")
        print("\n  3. Read documentation:")
        print("     README.md")
        print("     API_FIXES_COMPLETE.md")
        return 0
    else:
        print("[FAILED] Please fix the issues above")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
