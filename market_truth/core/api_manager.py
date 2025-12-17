"""
Centralized API Client Manager
Coordinates all API access with proper rate limiting, fallback, and tracking

Philosophy: Single source of truth for all market data APIs
"""

import os
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.fmp_client import FMPClient
from src.sec_edgar_client import SECEdgarClient
from src.yfinance_helper import yf_helper

try:
    from src.api_call_tracker import api_tracker
    HAS_TRACKER = True
except:
    HAS_TRACKER = False
    print("[Warning] API call tracker not available")

# Load environment variables
load_dotenv()


class APIManager:
    """
    Centralized API client manager

    Features:
    - Manages all API clients (FMP, SEC, yfinance)
    - Coordinated rate limiting
    - Automatic fallback chain
    - Usage tracking
    - Data quality indicators
    """

    def __init__(self):
        """Initialize all API clients with proper configuration"""

        # Get SEC user email from environment
        self.sec_user_email = os.getenv('SEC_USER_EMAIL', 'user@example.com')

        # Initialize clients
        self.fmp_client = None
        self.sec_client = None
        self.yf_helper = yf_helper

        # Rate limiting
        self.last_fmp_call = 0
        self.last_sec_call = 0
        self.last_yf_call = 0

        self.fmp_delay = 0.2  # 5 requests/second
        self.sec_delay = 0.15  # ~6 requests/second (under 10/s limit)
        self.yf_delay = 0.5   # Conservative for yfinance

        # Initialize clients
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients with error handling"""

        # 1. FMP Client (PRIMARY)
        try:
            self.fmp_client = FMPClient()
            print("[+] FMP API client initialized")
            print("[!] WARNING: FMP legacy endpoints deprecated (Aug 2025)")
            print("[!] Disabling FMP, using yfinance as primary")
            self.fmp_client = None  # Temporarily disable due to API changes
        except Exception as e:
            print(f"[!] FMP API not available: {e}")
            self.fmp_client = None

        # 2. SEC EDGAR Client
        try:
            user_agent = f"Mozilla/5.0 ({self.sec_user_email})"
            self.sec_client = SECEdgarClient(user_agent=user_agent)
            print(f"[+] SEC EDGAR client initialized (email: {self.sec_user_email})")
        except Exception as e:
            print(f"[!] SEC EDGAR client error: {e}")
            self.sec_client = None

        # 3. yfinance (FALLBACK)
        print("[+] yfinance helper available")

    def _rate_limit_fmp(self):
        """Rate limit FMP API calls"""
        elapsed = time.time() - self.last_fmp_call
        if elapsed < self.fmp_delay:
            time.sleep(self.fmp_delay - elapsed)
        self.last_fmp_call = time.time()

    def _rate_limit_sec(self):
        """Rate limit SEC API calls"""
        elapsed = time.time() - self.last_sec_call
        if elapsed < self.sec_delay:
            time.sleep(self.sec_delay - elapsed)
        self.last_sec_call = time.time()

    def _rate_limit_yf(self):
        """Rate limit yfinance calls"""
        elapsed = time.time() - self.last_yf_call
        if elapsed < self.yf_delay:
            time.sleep(self.yf_delay - elapsed)
        self.last_yf_call = time.time()

    def get_stock_data(self, ticker: str, use_fmp: bool = True) -> Dict[str, Any]:
        """
        Get stock data with automatic fallback

        Priority:
        1. FMP (if available and use_fmp=True)
        2. yfinance (always available)

        Returns:
            {
                'data': stock_object,
                'source': 'FMP' | 'YFINANCE',
                'quality': 'PRIMARY' | 'FALLBACK'
            }
        """

        # Try FMP first (if enabled and available)
        if use_fmp and self.fmp_client:
            try:
                self._rate_limit_fmp()
                profile = self.fmp_client.get_profile(ticker)
                if profile:
                    return {
                        'data': profile,
                        'source': 'FMP',
                        'quality': 'PRIMARY',
                        'client': self.fmp_client
                    }
            except Exception as e:
                print(f"[!] FMP failed for {ticker}: {e}")

        # Fallback to yfinance
        try:
            self._rate_limit_yf()
            stock = self.yf_helper.get_ticker(ticker)
            return {
                'data': stock,
                'source': 'YFINANCE',
                'quality': 'FALLBACK',
                'client': self.yf_helper
            }
        except Exception as e:
            print(f"[!] yfinance failed for {ticker}: {e}")
            return {
                'data': None,
                'source': 'NONE',
                'quality': 'ERROR',
                'error': str(e)
            }

    def get_financial_statements(self, ticker: str) -> Dict[str, Any]:
        """
        Get financial statements with FMP priority

        Returns comprehensive financial data from best available source
        """

        result = {
            'ticker': ticker,
            'source': None,
            'quality': None,
            'income_statement': None,
            'balance_sheet': None,
            'cash_flow': None,
            'error': None
        }

        # Try FMP first (best data quality)
        if self.fmp_client:
            try:
                self._rate_limit_fmp()
                income = self.fmp_client.get_income_statement(ticker, period='annual', limit=5)

                self._rate_limit_fmp()
                balance = self.fmp_client.get_balance_sheet(ticker, period='annual', limit=5)

                self._rate_limit_fmp()
                cash_flow = self.fmp_client.get_cash_flow_statement(ticker, period='annual', limit=5)

                if income or balance or cash_flow:
                    result['source'] = 'FMP'
                    result['quality'] = 'PRIMARY'
                    result['income_statement'] = income
                    result['balance_sheet'] = balance
                    result['cash_flow'] = cash_flow
                    return result

            except Exception as e:
                print(f"[!] FMP financials failed: {e}")

        # Fallback to yfinance
        try:
            self._rate_limit_yf()
            stock = self.yf_helper.get_ticker(ticker)

            result['source'] = 'YFINANCE'
            result['quality'] = 'FALLBACK'
            result['income_statement'] = stock.financials
            result['balance_sheet'] = stock.balance_sheet
            result['cash_flow'] = stock.cashflow

            return result

        except Exception as e:
            result['error'] = str(e)
            return result

    def get_sec_data(self, ticker: str) -> Dict[str, Any]:
        """
        Get SEC filing data

        Returns latest 10-K, proxy, and insider transactions
        """

        if not self.sec_client:
            return {
                'error': 'SEC client not available',
                'has_data': False
            }

        try:
            # Get CIK
            self._rate_limit_sec()
            cik = self.sec_client.get_cik_from_ticker(ticker)

            if not cik:
                return {
                    'error': 'CIK not found',
                    'has_data': False
                }

            # Get latest 10-K
            self._rate_limit_sec()
            filing_10k = self.sec_client.get_latest_10k(ticker)

            # Get latest proxy
            self._rate_limit_sec()
            proxy = self.sec_client.get_latest_proxy(ticker)

            # Get insider transactions
            self._rate_limit_sec()
            insider_filings = self.sec_client.get_insider_transactions(ticker, days_back=180)

            return {
                'has_data': True,
                'cik': cik,
                'latest_10k': filing_10k,
                'latest_proxy': proxy,
                'insider_filings': insider_filings,
                'insider_filings_count': len(insider_filings) if insider_filings else 0,
                'source': 'SEC_EDGAR',
                'quality': 'PRIMARY'
            }

        except Exception as e:
            return {
                'error': str(e),
                'has_data': False
            }

    def get_api_status(self) -> Dict[str, bool]:
        """
        Check status of all API clients

        Returns availability of each client
        """
        return {
            'fmp_available': self.fmp_client is not None,
            'sec_available': self.sec_client is not None,
            'yfinance_available': True,  # Always available
            'tracker_available': HAS_TRACKER
        }


# Singleton instance
_api_manager = None

def get_api_manager() -> APIManager:
    """Get singleton API manager instance"""
    global _api_manager
    if _api_manager is None:
        _api_manager = APIManager()
    return _api_manager


# Test
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python api_manager.py TICKER")
        print("\nExample: python api_manager.py AAPL")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    print(f"\n{'='*80}")
    print(f"API MANAGER TEST: {ticker}")
    print(f"{'='*80}\n")

    manager = get_api_manager()

    # Check API status
    print("API Status:")
    status = manager.get_api_status()
    for api, available in status.items():
        status_icon = "+" if available else "x"
        print(f"  [{status_icon}] {api}: {available}")

    # Test stock data
    print(f"\nFetching stock data for {ticker}...")
    stock_data = manager.get_stock_data(ticker)
    print(f"  Source: {stock_data['source']}")
    print(f"  Quality: {stock_data['quality']}")

    # Test financial statements
    print(f"\nFetching financial statements...")
    financials = manager.get_financial_statements(ticker)
    print(f"  Source: {financials['source']}")
    print(f"  Quality: {financials['quality']}")

    # Test SEC data
    print(f"\nFetching SEC data...")
    sec_data = manager.get_sec_data(ticker)
    if sec_data.get('has_data'):
        print(f"  CIK: {sec_data.get('cik')}")
        print(f"  10-K: {sec_data.get('latest_10k', {}).get('filing_date', 'N/A')}")
        print(f"  Insider filings: {sec_data.get('insider_filings_count', 0)}")
    else:
        print(f"  Error: {sec_data.get('error')}")

    print(f"\n{'='*80}\n")
