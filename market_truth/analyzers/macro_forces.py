"""
Layer 7: Macro Forces & Market Environment
Understanding the wind at your back or in your face

Analyzes:
1. Interest Rate Sensitivity - How exposed to rate changes?
2. Economic Cycle Position - Early, mid, or late cycle?
3. Beta & Volatility - Market correlation
4. Valuation Environment - Expensive or cheap relative to history?

Key Questions:
- Are we in a risk-on or risk-off environment?
- Is this stock benefiting from or hurt by current macro trends?
- What's the valuation regime (growth premium vs value)?
- How does this perform in different economic scenarios?

Green Flags:
- Macro tailwinds (e.g., tech in low rates)
- Low correlation to market (diversification)
- Reasonable valuation (not extreme)
- Secular trend alignment

Red Flags:
- Macro headwinds (e.g., growth stocks in rising rates)
- Extreme valuation (bubble territory)
- High beta in volatile markets
- Cyclical exposure at peak
"""
from src.yfinance_helper import yf_helper
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MacroForcesAnalyzer:
    """
    Analyze macro forces and market environment

    Philosophy: Don't fight the Fed. Don't fight the tape.
    Understanding the macro backdrop is critical.
    """

    def __init__(self, api_manager=None):
        self.api_manager = api_manager

    def analyze(self, ticker: str) -> Dict:
        """
        Complete macro forces analysis

        Returns comprehensive analysis with score 0-10
        """
        print(f"\n{'='*80}")
        print(f"MACRO FORCES ANALYSIS: {ticker}")
        print(f"{'='*80}\n")

        try:
            stock = yf_helper.get_ticker(ticker)
            info = stock.info

            analysis = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'score': 0,
                'rate_sensitivity': {},
                'market_correlation': {},
                'valuation_analysis': {},
                'economic_exposure': {},
                'red_flags': [],
                'green_flags': [],
                'warnings': []
            }

            # 1. Interest Rate Sensitivity
            print("Analyzing interest rate sensitivity...")
            rate_sens = self.analyze_rate_sensitivity(stock, info)
            analysis['rate_sensitivity'] = rate_sens

            # 2. Market Correlation (Beta)
            print("Analyzing market correlation...")
            correlation = self.analyze_market_correlation(stock, info)
            analysis['market_correlation'] = correlation

            # 3. Valuation Analysis
            print("Analyzing valuation environment...")
            valuation = self.analyze_valuation(stock, info)
            analysis['valuation_analysis'] = valuation

            # 4. Economic Cycle Exposure
            print("Analyzing economic cycle exposure...")
            economic = self.analyze_economic_exposure(stock, info)
            analysis['economic_exposure'] = economic

            # Calculate score
            score = self._calculate_score(analysis)
            analysis['score'] = score

            print(f"\nMacro Forces Score: {score}/10")

            return analysis

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return {
                'ticker': ticker,
                'score': 0,
                'error': str(e),
                'red_flags': ['ANALYSIS_FAILED']
            }

    def analyze_rate_sensitivity(self, stock, info: Dict) -> Dict:
        """
        Analyze sensitivity to interest rates

        High Rate Sensitivity:
        - High debt companies
        - Long-duration growth stocks
        - Unprofitable companies burning cash

        Low Rate Sensitivity:
        - Cash-rich companies
        - Value stocks
        - Profitable with low debt
        """
        analysis = {
            'sensitivity_rating': None,
            'debt_to_equity': None,
            'interest_coverage': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            # Debt metrics
            debt_to_equity = info.get('debtToEquity')
            total_debt = info.get('totalDebt', 0)
            total_cash = info.get('totalCash', 0)
            ebitda = info.get('ebitda', 0)

            if debt_to_equity is not None:
                analysis['debt_to_equity'] = round(debt_to_equity, 2)

                # High debt = high rate sensitivity
                if debt_to_equity > 200:  # >2x debt to equity
                    analysis['sensitivity_rating'] = 'VERY_HIGH'
                    analysis['red_flags'].append('HIGH_DEBT_RATE_SENSITIVE')
                elif debt_to_equity > 100:
                    analysis['sensitivity_rating'] = 'HIGH'
                    analysis['warnings'] = ['MODERATE_RATE_SENSITIVITY']
                elif debt_to_equity < 50:  # Low debt
                    analysis['sensitivity_rating'] = 'LOW'
                    analysis['green_flags'].append('LOW_RATE_SENSITIVITY')
                else:
                    analysis['sensitivity_rating'] = 'MODERATE'

            # Net cash position
            if total_cash and total_debt:
                net_cash = total_cash - total_debt
                analysis['net_cash_debt'] = net_cash

                if net_cash > 0:
                    analysis['green_flags'].append('NET_CASH_POSITION')
                    analysis['note'] = 'Cash-rich = low rate sensitivity'

            # Profitability (unprofitable = rate sensitive)
            net_income = info.get('netIncomeToCommon', 0)
            if net_income and net_income < 0:
                analysis['warnings'] = analysis.get('warnings', []) + ['UNPROFITABLE_RATE_SENSITIVE']

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_market_correlation(self, stock, info: Dict) -> Dict:
        """
        Analyze correlation to market (Beta)

        Beta Interpretation:
        - Beta > 1.5: Very high volatility vs market
        - Beta 1.0-1.5: Above market volatility
        - Beta 0.5-1.0: Below market volatility
        - Beta < 0.5: Low correlation (defensive)
        - Beta < 0: Inverse correlation (rare)
        """
        analysis = {
            'beta': None,
            'beta_rating': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            beta = info.get('beta')

            if beta is not None:
                analysis['beta'] = round(beta, 2)

                # Interpret beta
                if beta > 2.0:
                    analysis['beta_rating'] = 'EXTREMELY_VOLATILE'
                    analysis['red_flags'].append('VERY_HIGH_BETA')
                    analysis['note'] = 'Amplifies market moves significantly'
                elif beta > 1.5:
                    analysis['beta_rating'] = 'VERY_VOLATILE'
                    analysis['warnings'] = ['HIGH_BETA']
                elif beta > 1.0:
                    analysis['beta_rating'] = 'ABOVE_MARKET'
                elif beta > 0.5:
                    analysis['beta_rating'] = 'BELOW_MARKET'
                    analysis['green_flags'].append('DEFENSIVE_BETA')
                else:
                    analysis['beta_rating'] = 'DEFENSIVE'
                    analysis['green_flags'].append('VERY_DEFENSIVE')

                # In volatile markets, low beta is good
                # In bull markets, high beta can be good
                # Context matters - we'll note both aspects

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_valuation(self, stock, info: Dict) -> Dict:
        """
        Analyze valuation relative to fundamentals

        Multiple Metrics:
        - P/E ratio (price to earnings)
        - P/S ratio (price to sales)
        - P/B ratio (price to book)
        - PEG ratio (P/E to growth)

        Context: What's "expensive" depends on growth and industry
        """
        analysis = {
            'pe_ratio': None,
            'ps_ratio': None,
            'peg_ratio': None,
            'valuation_rating': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            # P/E Ratio
            pe_ratio = info.get('trailingPE')
            forward_pe = info.get('forwardPE')

            if pe_ratio:
                analysis['pe_ratio'] = round(pe_ratio, 2)

                # Context-dependent interpretation
                # Tech/Growth: P/E 20-40 normal, >60 expensive
                # Value: P/E 10-20 normal, >25 expensive

                if pe_ratio > 100:
                    analysis['warnings'] = analysis.get('warnings', []) + ['VERY_HIGH_PE']
                elif pe_ratio > 50:
                    analysis['warnings'] = analysis.get('warnings', []) + ['HIGH_PE']
                elif pe_ratio < 15:
                    analysis['green_flags'].append('REASONABLE_VALUATION')

            if forward_pe:
                analysis['forward_pe'] = round(forward_pe, 2)

            # P/S Ratio
            ps_ratio = info.get('priceToSalesTrailing12Months')
            if ps_ratio:
                analysis['ps_ratio'] = round(ps_ratio, 2)

                # Generally, P/S > 10 is expensive for most industries
                if ps_ratio > 20:
                    analysis['red_flags'].append('EXTREME_PS_RATIO')
                elif ps_ratio > 10:
                    analysis['warnings'] = analysis.get('warnings', []) + ['HIGH_PS_RATIO']

            # PEG Ratio (P/E / Growth)
            peg_ratio = info.get('pegRatio')
            if peg_ratio:
                analysis['peg_ratio'] = round(peg_ratio, 2)

                # PEG interpretation:
                # < 1.0 = undervalued relative to growth
                # 1.0-2.0 = fairly valued
                # > 2.0 = overvalued relative to growth

                if peg_ratio < 1.0:
                    analysis['green_flags'].append('ATTRACTIVE_PEG')
                    analysis['valuation_rating'] = 'UNDERVALUED'
                elif peg_ratio < 2.0:
                    analysis['valuation_rating'] = 'FAIR_VALUE'
                else:
                    analysis['valuation_rating'] = 'OVERVALUED'
                    analysis['warnings'] = analysis.get('warnings', []) + ['HIGH_PEG']

            # Price to Book
            pb_ratio = info.get('priceToBook')
            if pb_ratio:
                analysis['pb_ratio'] = round(pb_ratio, 2)

            # Overall valuation assessment
            if not analysis['valuation_rating']:
                # Fallback if no PEG
                if pe_ratio and pe_ratio < 15:
                    analysis['valuation_rating'] = 'REASONABLE'
                elif pe_ratio and pe_ratio > 50:
                    analysis['valuation_rating'] = 'EXPENSIVE'
                else:
                    analysis['valuation_rating'] = 'NEUTRAL'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_economic_exposure(self, stock, info: Dict) -> Dict:
        """
        Analyze exposure to economic cycles

        Economic Sensitivity:
        - Cyclical: Sensitive to economy (discretionary, industrial)
        - Defensive: Less sensitive (utilities, consumer staples, healthcare)
        - Growth: Secular trends override cycles (tech innovation)
        """
        analysis = {
            'sector': None,
            'economic_sensitivity': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')

            analysis['sector'] = sector
            analysis['industry'] = industry

            # Classify economic sensitivity
            defensive_sectors = [
                'Healthcare', 'Utilities', 'Consumer Defensive',
                'Consumer Staples'
            ]

            cyclical_sectors = [
                'Consumer Cyclical', 'Industrials', 'Materials',
                'Real Estate', 'Financial Services', 'Energy'
            ]

            growth_sectors = [
                'Technology', 'Communication Services'
            ]

            if sector in defensive_sectors:
                analysis['economic_sensitivity'] = 'DEFENSIVE'
                analysis['green_flags'].append('DEFENSIVE_SECTOR')
                analysis['note'] = 'Performs well in recessions'
            elif sector in cyclical_sectors:
                analysis['economic_sensitivity'] = 'CYCLICAL'
                analysis['warnings'] = ['CYCLICAL_EXPOSURE']
                analysis['note'] = 'Sensitive to economic cycles'
            elif sector in growth_sectors:
                analysis['economic_sensitivity'] = 'GROWTH'
                analysis['note'] = 'Secular growth trends'
            else:
                analysis['economic_sensitivity'] = 'UNKNOWN'

            # Revenue stability
            revenue_growth = info.get('revenueGrowth', 0)
            if revenue_growth and revenue_growth < -0.10:  # -10% revenue drop
                analysis['warnings'] = analysis.get('warnings', []) + ['REVENUE_DECLINE']

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _calculate_score(self, analysis: Dict) -> int:
        """
        Calculate overall macro forces score (0-10)

        Weighting:
        - Rate sensitivity: 0-3 points (favorable environment)
        - Market correlation: 0-2 points (risk management)
        - Valuation: 0-3 points (not overpaying)
        - Economic exposure: 0-2 points (cycle alignment)
        """
        score = 5  # Start neutral

        # Rate Sensitivity (0-3 points)
        # In current environment, lower sensitivity is better
        rate_data = analysis.get('rate_sensitivity', {})
        sensitivity = rate_data.get('sensitivity_rating', '')

        if sensitivity == 'LOW':
            score += 2
        elif sensitivity == 'VERY_HIGH':
            score -= 2

        # Net cash is always good
        if 'NET_CASH_POSITION' in rate_data.get('green_flags', []):
            score += 1

        # Market Correlation (0-2 points)
        # Moderate beta is generally best for risk/reward
        correlation_data = analysis.get('market_correlation', {})
        beta = correlation_data.get('beta', 1.0)

        if beta and 0.8 <= beta <= 1.2:  # Near market beta
            score += 1
        elif beta and beta < 0.8:  # Defensive
            score += 2
        elif beta and beta > 2.0:  # Very volatile
            score -= 1

        # Valuation (0-3 points)
        valuation_data = analysis.get('valuation_analysis', {})
        val_rating = valuation_data.get('valuation_rating', '')

        if val_rating == 'UNDERVALUED':
            score += 3
        elif val_rating == 'FAIR_VALUE':
            score += 1
        elif val_rating == 'OVERVALUED':
            score -= 2

        peg = valuation_data.get('peg_ratio')
        if peg and peg < 1.0:
            score += 1

        # Economic Exposure (0-2 points)
        economic_data = analysis.get('economic_exposure', {})
        sensitivity = economic_data.get('economic_sensitivity', '')

        # Defensive is always good
        if sensitivity == 'DEFENSIVE':
            score += 2
        # Cyclical is risky at cycle peaks
        elif sensitivity == 'CYCLICAL':
            score -= 1

        # Collect all flags
        all_red_flags = []
        all_green_flags = []
        all_warnings = []

        for category in ['rate_sensitivity', 'market_correlation', 'valuation_analysis', 'economic_exposure']:
            if category in analysis:
                cat_data = analysis[category]
                if isinstance(cat_data, dict):
                    all_red_flags.extend(cat_data.get('red_flags', []))
                    all_green_flags.extend(cat_data.get('green_flags', []))
                    all_warnings.extend(cat_data.get('warnings', []))

        analysis['red_flags'] = list(set(all_red_flags))
        analysis['green_flags'] = list(set(all_green_flags))
        analysis['warnings'] = list(set(all_warnings))

        # Penalty for extreme red flags
        if 'EXTREME_PS_RATIO' in all_red_flags:
            score -= 2

        # Cap at 0-10
        return max(0, min(10, score))


def main():
    """Test the analyzer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python macro_forces_analyzer.py <TICKER>")
        print("\nExample: python macro_forces_analyzer.py NVDA")
        return

    ticker = sys.argv[1].upper()

    analyzer = MacroForcesAnalyzer()
    result = analyzer.analyze(ticker)

    # Display results
    print(f"\n{'='*80}")
    print(f"MACRO FORCES ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    print(f"Overall Score: {result['score']}/10\n")

    # Rate Sensitivity
    if 'rate_sensitivity' in result:
        rate = result['rate_sensitivity']
        print("INTEREST RATE SENSITIVITY:")
        if rate.get('sensitivity_rating'):
            print(f"  Sensitivity Rating: {rate['sensitivity_rating']}")
        if rate.get('debt_to_equity') is not None:
            print(f"  Debt to Equity: {rate['debt_to_equity']}")
        if rate.get('net_cash_debt'):
            net = rate['net_cash_debt']
            print(f"  Net Cash/(Debt): ${net / 1e9:.1f}B")
        if rate.get('note'):
            print(f"  Note: {rate['note']}")

    # Market Correlation
    if 'market_correlation' in result:
        corr = result['market_correlation']
        print(f"\nMARKET CORRELATION:")
        if corr.get('beta') is not None:
            print(f"  Beta: {corr['beta']}")
        if corr.get('beta_rating'):
            print(f"  Beta Rating: {corr['beta_rating']}")
        if corr.get('note'):
            print(f"  Note: {corr['note']}")

    # Valuation
    if 'valuation_analysis' in result:
        val = result['valuation_analysis']
        print(f"\nVALUATION:")
        if val.get('pe_ratio'):
            print(f"  P/E Ratio: {val['pe_ratio']}")
        if val.get('forward_pe'):
            print(f"  Forward P/E: {val['forward_pe']}")
        if val.get('ps_ratio'):
            print(f"  P/S Ratio: {val['ps_ratio']}")
        if val.get('peg_ratio'):
            print(f"  PEG Ratio: {val['peg_ratio']}")
        if val.get('pb_ratio'):
            print(f"  P/B Ratio: {val['pb_ratio']}")
        if val.get('valuation_rating'):
            print(f"  Valuation Rating: {val['valuation_rating']}")

    # Economic Exposure
    if 'economic_exposure' in result:
        econ = result['economic_exposure']
        print(f"\nECONOMIC EXPOSURE:")
        if econ.get('sector'):
            print(f"  Sector: {econ['sector']}")
        if econ.get('economic_sensitivity'):
            print(f"  Economic Sensitivity: {econ['economic_sensitivity']}")
        if econ.get('note'):
            print(f"  Note: {econ['note']}")

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
