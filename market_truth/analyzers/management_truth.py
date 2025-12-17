"""
Layer 4: Management Truth Detection
Are they competent? Are they honest?

Analyzes:
1. Skin in the Game Test - Do insiders believe in the company?
2. Insider Ownership - How much do they personally own?
3. Compensation Structure - What behavior are they incentivized for?

Key Questions:
- Are insiders buying or selling?
- Do executives own meaningful stakes?
- Is compensation aligned with long-term value creation?

Red Flags:
- Multiple executives selling near highs
- CEO owns <1% of company
- Compensation tied to short-term metrics
- Options grants while stock falling
"""
from src.yfinance_helper import yf_helper
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import sys
import os

# Import SEC client
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.sec_edgar_client import SECEdgarClient


class ManagementTruthDetector:
    """
    Detect management quality and alignment with shareholders

    Philosophy: Watch what they DO, not what they SAY

    Data Sources (Priority Order):
    1. PRIMARY: SEC EDGAR (DEF 14A proxy, Form 4 insider trades)
    2. FALLBACK: yfinance (convenience, may be stale)
    3. ERROR: Clear indication when data unavailable
    """

    def __init__(self, api_manager=None):
        self.api_manager = api_manager
        # Use SEC client from API manager if available
        if api_manager and api_manager.sec_client:
            self.sec_client = api_manager.sec_client
        else:
            # Fallback to creating own client
            self.sec_client = SECEdgarClient()
        self.data_quality = 'UNKNOWN'

    def analyze(self, ticker: str) -> Dict:
        """
        Complete management truth analysis

        Returns comprehensive analysis with score 0-10
        """
        print(f"\n{'='*80}")
        print(f"MANAGEMENT TRUTH DETECTION: {ticker}")
        print(f"{'='*80}\n")

        try:
            # Use API manager if available
            if self.api_manager:
                stock_data = self.api_manager.get_stock_data(ticker)
                stock = stock_data['data']
            else:
                # Add delay to avoid rate limiting
                time.sleep(1)
                stock = yf_helper.get_ticker(ticker)

            # Try to get info with retry
            max_retries = 3
            info = None
            for attempt in range(max_retries):
                try:
                    info = stock.info
                    if info and 'symbol' in info:
                        break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                        print(f"Rate limit, waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        raise

            if not info:
                raise ValueError("Could not retrieve ticker info")

            analysis = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'score': 0,
                'insider_ownership': {},
                'insider_transactions': {},
                'sec_filings': {},
                'compensation': {},
                'management_quality': {},
                'red_flags': [],
                'green_flags': [],
                'warnings': [],
                'data_quality': 'UNKNOWN',
                'data_sources': []
            }

            # 0. Get SEC filing metadata (PRIMARY SOURCE)
            print("Fetching SEC filing data...")
            sec_data = self.get_sec_filing_data(ticker)
            analysis['sec_filings'] = sec_data
            if sec_data.get('has_data'):
                analysis['data_sources'].append('SEC_EDGAR')
                self.data_quality = 'PRIMARY'

            # 1. Insider Ownership Analysis
            print("Analyzing insider ownership...")
            ownership = self.analyze_insider_ownership(stock, info)
            analysis['insider_ownership'] = ownership

            # 2. Insider Transaction Analysis (SEC PRIMARY, yfinance FALLBACK)
            print("Analyzing insider transactions...")
            transactions = self.analyze_insider_transactions_multi_source(ticker, stock, info, sec_data)
            analysis['insider_transactions'] = transactions

            # 3. Compensation Analysis (limited public data)
            print("Analyzing compensation structure...")
            compensation = self.analyze_compensation(stock, info)
            analysis['compensation'] = compensation

            # 4. Management Quality Indicators
            print("Assessing management quality...")
            quality = self.assess_management_quality(stock, info)
            analysis['management_quality'] = quality

            # Calculate score
            score = self._calculate_score(analysis)
            analysis['score'] = score
            analysis['data_quality'] = self.data_quality

            # Add data source summary
            if 'yfinance' not in [s.lower() for s in analysis['data_sources']]:
                analysis['data_sources'].append('yfinance')

            print(f"\nManagement Truth Score: {score}/10")
            print(f"Data Quality: {self.data_quality}")
            print(f"Data Sources: {', '.join(analysis['data_sources'])}")

            return analysis

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return {
                'ticker': ticker,
                'score': 0,
                'error': str(e),
                'red_flags': ['ANALYSIS_FAILED']
            }

    def get_sec_filing_data(self, ticker: str) -> Dict:
        """
        Get SEC filing metadata for management analysis

        Returns:
            {
                'has_data': True/False,
                'latest_proxy': {...},
                'latest_10k': {...},
                'insider_filings_count': int,
                'data_quality': 'CURRENT/STALE/OLD'
            }
        """
        try:
            # Get latest proxy (DEF 14A) - contains exec comp data
            proxy = self.sec_client.get_latest_proxy(ticker)

            # Get latest 10-K - contains business context
            filing_10k = self.sec_client.get_latest_10k(ticker)

            # Get insider transactions (Form 4)
            insider_filings = self.sec_client.get_insider_transactions(ticker, days_back=180)

            has_data = bool(proxy or filing_10k or insider_filings)

            result = {
                'has_data': has_data,
                'latest_proxy': proxy,
                'latest_10k': filing_10k,
                'insider_filings': insider_filings,
                'insider_filings_count': len(insider_filings)
            }

            # Assess data quality based on filing dates
            if filing_10k:
                result['data_quality'] = self.sec_client.validate_data_quality(
                    filing_10k.get('filing_date', '')
                )
            else:
                result['data_quality'] = 'NO_DATA'

            return result

        except Exception as e:
            print(f"Error fetching SEC data: {e}")
            return {
                'has_data': False,
                'error': str(e),
                'data_quality': 'ERROR'
            }

    def analyze_insider_transactions_multi_source(self, ticker: str, stock,
                                                   info: Dict, sec_data: Dict) -> Dict:
        """
        Analyze insider transactions using SEC as primary, yfinance as fallback

        Priority:
        1. SEC Form 4 filings (most accurate, timely)
        2. yfinance insider transactions (convenience)
        """
        analysis = {
            'data_source': 'NONE',
            'recent_activity': 'No data available',
            'form4_count': 0,
            'red_flags': [],
            'green_flags': [],
            'warnings': []
        }

        # Try SEC first
        if sec_data.get('has_data') and sec_data.get('insider_filings'):
            filings = sec_data['insider_filings']
            analysis['form4_count'] = len(filings)
            analysis['data_source'] = 'SEC_EDGAR'

            if len(filings) > 0:
                analysis['recent_activity'] = f"{len(filings)} Form 4 filings in last 180 days"
                analysis['most_recent_filing'] = filings[0]['filing_date']

                # TODO: Parse actual Form 4 XML to determine buy vs sell
                # For now, just note that we have real SEC data
                analysis['green_flags'].append('SEC_FORM4_DATA_AVAILABLE')
                analysis['note'] = "Real-time SEC Form 4 data (filed within 2 business days of transaction)"

            return analysis

        # Fallback to yfinance
        analysis['data_source'] = 'YFINANCE_FALLBACK'
        yf_analysis = self.analyze_insider_transactions(stock, info)

        # Merge yfinance data with quality warning
        analysis.update(yf_analysis)
        analysis['warnings'].append('USING_YFINANCE_DATA')
        analysis['note'] = "Using yfinance data (may be incomplete or stale)"

        return analysis

    def analyze_insider_ownership(self, stock, info: Dict) -> Dict:
        """
        Analyze insider ownership percentages

        Key Metrics:
        - % held by insiders
        - % held by institutions
        - Float (public tradeable shares)

        Scoring:
        - CEO owns >5% = strong alignment
        - CEO owns 1-5% = decent alignment
        - CEO owns <1% = misaligned
        """
        analysis = {
            'insider_pct': None,
            'institutional_pct': None,
            'float_pct': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            # Get ownership data
            held_by_insiders = info.get('heldPercentInsiders')
            held_by_institutions = info.get('heldPercentInstitutions')

            if held_by_insiders is not None:
                insider_pct = held_by_insiders * 100
                analysis['insider_pct'] = round(insider_pct, 2)

                # Flags based on insider ownership
                if insider_pct > 20:
                    analysis['green_flags'].append('HIGH_INSIDER_OWNERSHIP')
                elif insider_pct > 10:
                    analysis['green_flags'].append('GOOD_INSIDER_OWNERSHIP')
                elif insider_pct < 1:
                    analysis['red_flags'].append('LOW_INSIDER_OWNERSHIP')

            if held_by_institutions is not None:
                inst_pct = held_by_institutions * 100
                analysis['institutional_pct'] = round(inst_pct, 2)

                # High institutional = professional money believes in it
                if inst_pct > 70:
                    analysis['green_flags'].append('HIGH_INSTITUTIONAL_OWNERSHIP')

            # Float analysis
            shares_outstanding = info.get('sharesOutstanding')
            float_shares = info.get('floatShares')

            if shares_outstanding and float_shares and shares_outstanding > 0:
                float_pct = (float_shares / shares_outstanding) * 100
                analysis['float_pct'] = round(float_pct, 2)

                # Low float can mean high insider/institutional control
                if float_pct < 50:
                    analysis['green_flags'].append('LOW_FLOAT_TIGHT_CONTROL')

            # Get major holders info
            try:
                major_holders = stock.major_holders
                if major_holders is not None and not major_holders.empty:
                    # major_holders is typically a 2-column df with % and description
                    analysis['major_holders_data'] = major_holders.to_dict()
            except:
                pass

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_insider_transactions(self, stock, info: Dict) -> Dict:
        """
        Analyze recent insider buying/selling

        This is LIMITED by yfinance - doesn't provide detailed Form 4 data
        For full analysis, would need to scrape SEC Edgar or use paid API

        What we can get:
        - General insider transaction summary from info
        - Would need external API for detailed transaction history
        """
        analysis = {
            'recent_activity': 'Limited data available',
            'note': 'Full insider transaction analysis requires SEC Edgar API',
            'red_flags': [],
            'green_flags': []
        }

        try:
            # yfinance has limited insider transaction data
            # For production, integrate with:
            # - SEC Edgar API for Form 4 filings
            # - OpenInsider.com scraping
            # - Paid data providers (Quiver Quantitative, etc.)

            # Check if there's any insider info available
            try:
                insider_transactions = stock.insider_transactions
                if insider_transactions is not None and not insider_transactions.empty:
                    # Analyze recent transactions (last 6 months)
                    recent = insider_transactions.head(20)  # Get recent transactions

                    # Count buys vs sells
                    if 'Shares' in recent.columns:
                        total_shares = recent['Shares'].sum()

                        if total_shares > 0:
                            analysis['recent_activity'] = f'Net buying: {total_shares:,.0f} shares'
                            analysis['green_flags'].append('INSIDER_BUYING')
                        elif total_shares < 0:
                            analysis['recent_activity'] = f'Net selling: {abs(total_shares):,.0f} shares'
                            analysis['warnings'] = analysis.get('warnings', []) + ['INSIDER_SELLING']

                    analysis['transaction_count'] = len(recent)
                else:
                    analysis['note'] = 'No insider transaction data available from yfinance'

            except Exception as e:
                analysis['note'] = f'Insider transactions unavailable: {str(e)}'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_compensation(self, stock, info: Dict) -> Dict:
        """
        Analyze executive compensation structure

        Data Availability:
        - Total compensation for top executives (from 10-K DEF 14A proxy)
        - yfinance provides limited compensation data
        - Full analysis requires scraping proxy statements

        What we look for:
        - Is compensation reasonable relative to company size?
        - Stock-based vs cash ratio (alignment)
        - Vesting schedules (long-term vs short-term incentives)
        """
        analysis = {
            'ceo_compensation': None,
            'compensation_ratio': None,
            'red_flags': [],
            'green_flags': [],
            'note': 'Detailed compensation analysis requires proxy statement (DEF 14A)'
        }

        try:
            # Limited data from yfinance
            # Would need to parse SEC filings for full analysis

            # Check for compensation in officer data
            try:
                # Get company officers
                officers = info.get('companyOfficers', [])

                if officers:
                    # Find CEO
                    ceo = next((officer for officer in officers
                               if 'CEO' in officer.get('title', '').upper()
                               or 'Chief Executive' in officer.get('title', '')), None)

                    if ceo:
                        total_pay = ceo.get('totalPay')
                        if total_pay:
                            analysis['ceo_compensation'] = total_pay

                            # Compare to company size (market cap)
                            market_cap = info.get('marketCap')
                            if market_cap and market_cap > 0:
                                # CEO pay as % of market cap
                                pay_ratio = (total_pay / market_cap) * 100

                                analysis['compensation_ratio'] = {
                                    'ceo_pay': total_pay,
                                    'market_cap': market_cap,
                                    'pay_pct_of_mcap': round(pay_ratio, 6)
                                }

                                # Reasonable CEO pay is typically 0.001% - 0.01% of market cap
                                # for large companies
                                if market_cap > 100e9:  # $100B+ company
                                    if pay_ratio > 0.001:
                                        analysis['warnings'] = analysis.get('warnings', []) + ['HIGH_CEO_COMPENSATION']
                                elif market_cap > 10e9:  # $10B+ company
                                    if pay_ratio > 0.01:
                                        analysis['warnings'] = analysis.get('warnings', []) + ['HIGH_CEO_COMPENSATION']

            except Exception as e:
                pass

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def assess_management_quality(self, stock, info: Dict) -> Dict:
        """
        Assess overall management quality using proxy indicators

        Indicators:
        - Company performance vs peers
        - Return on Equity (how efficiently management uses capital)
        - Profit margins (management execution quality)
        - Revenue growth consistency
        """
        analysis = {
            'performance_metrics': {},
            'red_flags': [],
            'green_flags': []
        }

        try:
            # Return on Equity - Key management efficiency metric
            roe = info.get('returnOnEquity')
            if roe:
                roe_pct = roe * 100
                analysis['performance_metrics']['return_on_equity'] = round(roe_pct, 2)

                if roe_pct > 20:  # >20% ROE = excellent capital allocation
                    analysis['green_flags'].append('EXCELLENT_ROE')
                elif roe_pct > 15:
                    analysis['green_flags'].append('STRONG_ROE')
                elif roe_pct < 10:
                    analysis['red_flags'].append('WEAK_ROE')

            # Return on Assets
            roa = info.get('returnOnAssets')
            if roa:
                roa_pct = roa * 100
                analysis['performance_metrics']['return_on_assets'] = round(roa_pct, 2)

                if roa_pct > 10:
                    analysis['green_flags'].append('EFFICIENT_ASSET_USE')

            # Profit Margin - Execution quality
            profit_margin = info.get('profitMargins')
            if profit_margin:
                margin_pct = profit_margin * 100
                analysis['performance_metrics']['profit_margin'] = round(margin_pct, 2)

                if margin_pct > 20:
                    analysis['green_flags'].append('HIGH_PROFITABILITY')
                elif margin_pct < 5:
                    analysis['red_flags'].append('LOW_PROFITABILITY')

            # Operating Margin - Core business efficiency
            operating_margin = info.get('operatingMargins')
            if operating_margin:
                op_margin_pct = operating_margin * 100
                analysis['performance_metrics']['operating_margin'] = round(op_margin_pct, 2)

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _calculate_score(self, analysis: Dict) -> int:
        """
        Calculate overall management truth score (0-10)

        Weighting:
        - Insider ownership: 0-3 points
        - Insider activity: 0-2 points
        - Management performance: 0-5 points
        """
        score = 5  # Start neutral

        # Insider Ownership (0-3 points)
        ownership = analysis.get('insider_ownership', {})
        insider_pct = ownership.get('insider_pct', 0)

        if insider_pct:
            if insider_pct > 20:
                score += 3
            elif insider_pct > 10:
                score += 2
            elif insider_pct > 5:
                score += 1
            elif insider_pct < 1:
                score -= 1

        # Management Performance (0-5 points)
        quality = analysis.get('management_quality', {})
        metrics = quality.get('performance_metrics', {})

        roe = metrics.get('return_on_equity', 0)
        if roe > 20:
            score += 2
        elif roe > 15:
            score += 1
        elif roe < 10 and roe > 0:
            score -= 1

        profit_margin = metrics.get('profit_margin', 0)
        if profit_margin > 20:
            score += 1
        elif profit_margin < 5 and profit_margin > 0:
            score -= 1

        # Collect all flags
        all_red_flags = []
        all_green_flags = []
        all_warnings = []

        for category in ['insider_ownership', 'insider_transactions', 'compensation', 'management_quality']:
            if category in analysis:
                cat_data = analysis[category]
                if isinstance(cat_data, dict):
                    all_red_flags.extend(cat_data.get('red_flags', []))
                    all_green_flags.extend(cat_data.get('green_flags', []))
                    all_warnings.extend(cat_data.get('warnings', []))

        analysis['red_flags'] = list(set(all_red_flags))
        analysis['green_flags'] = list(set(all_green_flags))
        analysis['warnings'] = list(set(all_warnings))

        # Bonus/penalty for flags
        score += min(len(all_green_flags), 2)  # Max +2 for green flags
        score -= len(all_red_flags)  # -1 for each red flag

        # Cap at 0-10
        return max(0, min(10, score))


def main():
    """Test the detector"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python management_truth_detector.py <TICKER>")
        print("\nExample: python management_truth_detector.py AAPL")
        return

    ticker = sys.argv[1].upper()

    detector = ManagementTruthDetector()
    result = detector.analyze(ticker)

    # Display results
    print(f"\n{'='*80}")
    print(f"MANAGEMENT TRUTH ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    print(f"Overall Score: {result['score']}/10\n")

    # Insider Ownership
    if 'insider_ownership' in result:
        own = result['insider_ownership']
        print("INSIDER OWNERSHIP:")
        if own.get('insider_pct') is not None:
            print(f"  Insiders: {own['insider_pct']:.2f}%")
        if own.get('institutional_pct') is not None:
            print(f"  Institutions: {own['institutional_pct']:.2f}%")
        if own.get('float_pct') is not None:
            print(f"  Public Float: {own['float_pct']:.2f}%")

    # Insider Transactions
    if 'insider_transactions' in result:
        trans = result['insider_transactions']
        print(f"\nINSIDER TRANSACTIONS:")
        print(f"  {trans.get('recent_activity', 'No data')}")
        if trans.get('transaction_count'):
            print(f"  Recent Count: {trans['transaction_count']} transactions")
        if trans.get('note'):
            print(f"  Note: {trans['note']}")

    # Management Performance
    if 'management_quality' in result:
        qual = result['management_quality']
        if 'performance_metrics' in qual:
            print(f"\nMANAGEMENT PERFORMANCE:")
            metrics = qual['performance_metrics']
            if metrics.get('return_on_equity'):
                print(f"  Return on Equity: {metrics['return_on_equity']:.2f}%")
            if metrics.get('return_on_assets'):
                print(f"  Return on Assets: {metrics['return_on_assets']:.2f}%")
            if metrics.get('profit_margin'):
                print(f"  Profit Margin: {metrics['profit_margin']:.2f}%")
            if metrics.get('operating_margin'):
                print(f"  Operating Margin: {metrics['operating_margin']:.2f}%")

    # Flags
    if result.get('green_flags'):
        print(f"\nGREEN FLAGS:")
        for flag in result['green_flags']:
            print(f"  + {flag}")

    if result.get('warnings'):
        print(f"\nWARNINGS:")
        for warning in result['warnings']:
            print(f"  ! {warning}")

    if result.get('red_flags'):
        print(f"\nRED FLAGS:")
        for flag in result['red_flags']:
            print(f"  - {flag}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
