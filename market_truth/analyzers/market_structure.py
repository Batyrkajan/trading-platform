"""
Layer 5: Market Structure & Incentives
Understanding the game board - who owns what and what are their incentives?

Analyzes:
1. Float Analysis - How much is actually tradeable?
2. Short Interest - Who's betting against it?
3. Options Activity - What are the gamma/delta dynamics?
4. Liquidity Analysis - Can you get in/out easily?

Key Questions:
- Is this a crowded trade?
- Are shorts underwater (squeeze potential)?
- Is float low (volatility potential)?
- Can institutions move this easily?

Green Flags:
- Low float + high institutional ownership = tight supply
- Rising short interest while stock rises = short squeeze setup
- High liquidity = easy entry/exit

Red Flags:
- Extremely high short interest (>30%) = something's wrong
- Low liquidity = can't exit when you need to
- Recent secondary offering = dilution
"""
from src.yfinance_helper import yf_helper
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MarketStructureAnalyzer:
    """
    Analyze market structure and trading dynamics

    Philosophy: The market is a game. Understand who the players are
    and what incentives they have.
    """

    def __init__(self, api_manager=None):
        self.api_manager = api_manager

    def analyze(self, ticker: str) -> Dict:
        """
        Complete market structure analysis

        Returns comprehensive analysis with score 0-10
        """
        print(f"\n{'='*80}")
        print(f"MARKET STRUCTURE ANALYSIS: {ticker}")
        print(f"{'='*80}\n")

        try:
            stock = yf_helper.get_ticker(ticker)
            info = stock.info

            analysis = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'score': 0,
                'float_analysis': {},
                'short_interest': {},
                'liquidity': {},
                'options_activity': {},
                'red_flags': [],
                'green_flags': [],
                'warnings': []
            }

            # 1. Float Analysis
            print("Analyzing float structure...")
            float_data = self.analyze_float(stock, info)
            analysis['float_analysis'] = float_data

            # 2. Short Interest Analysis
            print("Analyzing short interest...")
            short_data = self.analyze_short_interest(stock, info)
            analysis['short_interest'] = short_data

            # 3. Liquidity Analysis
            print("Analyzing liquidity...")
            liquidity_data = self.analyze_liquidity(stock, info)
            analysis['liquidity'] = liquidity_data

            # 4. Options Activity (limited by free data)
            print("Analyzing options activity...")
            options_data = self.analyze_options_activity(stock, info)
            analysis['options_activity'] = options_data

            # Calculate score
            score = self._calculate_score(analysis)
            analysis['score'] = score

            print(f"\nMarket Structure Score: {score}/10")

            return analysis

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return {
                'ticker': ticker,
                'score': 0,
                'error': str(e),
                'red_flags': ['ANALYSIS_FAILED']
            }

    def analyze_float(self, stock, info: Dict) -> Dict:
        """
        Analyze float structure

        Float = Shares available for public trading
        Lower float = Higher volatility potential

        Key Metrics:
        - Shares Outstanding vs Float
        - % held by insiders + institutions
        - Implied float % available for trading
        """
        analysis = {
            'shares_outstanding': None,
            'float_shares': None,
            'float_pct': None,
            'tradeable_float_pct': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            shares_outstanding = info.get('sharesOutstanding')
            float_shares = info.get('floatShares')

            if shares_outstanding and float_shares:
                analysis['shares_outstanding'] = shares_outstanding
                analysis['float_shares'] = float_shares

                # Float as % of outstanding
                float_pct = (float_shares / shares_outstanding) * 100
                analysis['float_pct'] = round(float_pct, 2)

                # Calculate tradeable float (after insider/institutional holdings)
                insider_pct = info.get('heldPercentInsiders', 0) * 100
                institutional_pct = info.get('heldPercentInstitutions', 0) * 100

                # Tradeable float = total float - what's locked up
                locked_up_pct = insider_pct + institutional_pct
                tradeable_float_pct = max(0, float_pct - locked_up_pct)
                analysis['tradeable_float_pct'] = round(tradeable_float_pct, 2)

                # Flags based on float structure
                if tradeable_float_pct < 20:
                    analysis['green_flags'].append('LOW_TRADEABLE_FLOAT')
                    analysis['note'] = 'Low float = high volatility potential'
                elif tradeable_float_pct > 80:
                    analysis['warnings'] = ['HIGH_FLOAT_LOW_CONTROL']

                # Very low float can be manipulated
                if tradeable_float_pct < 10:
                    analysis['warnings'] = analysis.get('warnings', []) + ['EXTREMELY_LOW_FLOAT']

                # Share count
                analysis['shares_outstanding_formatted'] = f"{shares_outstanding:,.0f}"
                analysis['float_shares_formatted'] = f"{float_shares:,.0f}"

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_short_interest(self, stock, info: Dict) -> Dict:
        """
        Analyze short interest

        Short Interest = % of float sold short
        High short interest can lead to squeezes

        Key Metrics:
        - Short % of Float
        - Short % of Shares Outstanding
        - Short Ratio (days to cover)

        Interpretation:
        - <5% = Normal
        - 5-10% = Elevated
        - 10-20% = High (squeeze potential)
        - >20% = Extreme (either fraud or squeeze setup)
        """
        analysis = {
            'short_percent_float': None,
            'short_percent_outstanding': None,
            'short_ratio': None,
            'red_flags': [],
            'green_flags': [],
            'warnings': []
        }

        try:
            # Get short data from info
            short_pct_float = info.get('shortPercentOfFloat')
            short_ratio = info.get('shortRatio')

            if short_pct_float is not None:
                short_pct = short_pct_float * 100
                analysis['short_percent_float'] = round(short_pct, 2)

                # Interpret short interest
                if short_pct < 5:
                    analysis['interpretation'] = 'Normal short interest'
                elif short_pct < 10:
                    analysis['interpretation'] = 'Elevated short interest'
                    analysis['green_flags'].append('MODERATE_SHORT_INTEREST')
                elif short_pct < 20:
                    analysis['interpretation'] = 'High short interest - squeeze potential'
                    analysis['green_flags'].append('SQUEEZE_POTENTIAL')
                else:
                    analysis['interpretation'] = 'Extreme short interest - investigate why'
                    analysis['warnings'].append('EXTREME_SHORT_INTEREST')
                    analysis['note'] = 'Either fraud concerns or epic squeeze setup'

            if short_ratio is not None:
                analysis['short_ratio'] = round(short_ratio, 2)
                analysis['days_to_cover'] = round(short_ratio, 1)

                # Days to cover interpretation
                if short_ratio > 10:
                    analysis['green_flags'].append('HIGH_DAYS_TO_COVER')
                    analysis['squeeze_risk'] = 'Very high - shorts need many days to cover'
                elif short_ratio > 5:
                    analysis['squeeze_risk'] = 'Moderate - could squeeze on volume spike'
                else:
                    analysis['squeeze_risk'] = 'Low - shorts can cover quickly'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_liquidity(self, stock, info: Dict) -> Dict:
        """
        Analyze trading liquidity

        Liquidity = How easily can you buy/sell without moving price

        Key Metrics:
        - Average Volume
        - Volume vs Market Cap ratio
        - Bid-Ask Spread (not available in yfinance)

        Good Liquidity:
        - Average volume > 1M shares/day
        - Volume > 0.1% of market cap daily
        """
        analysis = {
            'avg_volume': None,
            'volume_to_mcap_ratio': None,
            'liquidity_score': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            avg_volume = info.get('averageVolume')
            market_cap = info.get('marketCap')

            if avg_volume:
                analysis['avg_volume'] = avg_volume
                analysis['avg_volume_formatted'] = f"{avg_volume:,.0f}"

                # Volume interpretation
                if avg_volume > 10_000_000:
                    analysis['liquidity_rating'] = 'EXCELLENT'
                    analysis['green_flags'].append('HIGH_LIQUIDITY')
                elif avg_volume > 1_000_000:
                    analysis['liquidity_rating'] = 'GOOD'
                elif avg_volume > 100_000:
                    analysis['liquidity_rating'] = 'MODERATE'
                    analysis['warnings'] = ['MODERATE_LIQUIDITY']
                else:
                    analysis['liquidity_rating'] = 'LOW'
                    analysis['red_flags'].append('LOW_LIQUIDITY')

                # Volume to market cap ratio
                if market_cap and market_cap > 0:
                    volume_mcap_ratio = (avg_volume * info.get('currentPrice', 0)) / market_cap
                    analysis['volume_to_mcap_ratio'] = round(volume_mcap_ratio * 100, 4)

                    if volume_mcap_ratio > 0.01:  # >1% of market cap trades daily
                        analysis['green_flags'].append('HIGH_TURNOVER')
                    elif volume_mcap_ratio < 0.001:  # <0.1% trades daily
                        analysis['warnings'] = analysis.get('warnings', []) + ['LOW_TURNOVER']

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_options_activity(self, stock, info: Dict) -> Dict:
        """
        Analyze options market activity

        Limited by free data availability
        Full analysis would require:
        - Put/Call ratio
        - Options volume vs stock volume
        - Gamma exposure
        - Max pain analysis

        What we can get from yfinance:
        - Check if options are available
        - Implied volatility (if available)
        """
        analysis = {
            'options_available': False,
            'note': 'Full options flow analysis requires paid data',
            'red_flags': [],
            'green_flags': []
        }

        try:
            # Check if options are available
            try:
                options_dates = stock.options
                if options_dates and len(options_dates) > 0:
                    analysis['options_available'] = True
                    analysis['expiration_dates_count'] = len(options_dates)

                    # Having options is generally good (more liquidity, hedging tools)
                    analysis['green_flags'].append('OPTIONS_AVAILABLE')

                    # Could expand this to analyze specific options chains
                    # But would need careful rate limiting with yfinance
                else:
                    analysis['options_available'] = False
                    analysis['warnings'] = ['NO_OPTIONS_AVAILABLE']
            except:
                analysis['options_available'] = False
                analysis['note'] = 'Options data unavailable'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _calculate_score(self, analysis: Dict) -> int:
        """
        Calculate overall market structure score (0-10)

        Weighting:
        - Float structure: 0-3 points
        - Short interest: 0-2 points
        - Liquidity: 0-3 points
        - Options availability: 0-2 points
        """
        score = 5  # Start neutral

        # Float Analysis (0-3 points)
        float_data = analysis.get('float_analysis', {})
        tradeable_float = float_data.get('tradeable_float_pct', 50)

        if tradeable_float:
            if 20 < tradeable_float < 60:  # Sweet spot - not too tight, not too loose
                score += 2
            elif tradeable_float < 20:  # Low float - volatile but interesting
                score += 1
            elif tradeable_float < 10:  # Too low - manipulation risk
                score -= 1

        # Short Interest (0-2 points)
        short_data = analysis.get('short_interest', {})
        short_pct = short_data.get('short_percent_float', 0)

        if short_pct:
            if 10 < short_pct < 30:  # Squeeze potential without fraud concerns
                score += 2
            elif 5 < short_pct < 10:  # Moderate short interest
                score += 1
            elif short_pct > 40:  # Extreme - likely fraud concerns
                score -= 2

        # Liquidity (0-3 points)
        liquidity_data = analysis.get('liquidity', {})
        liquidity_rating = liquidity_data.get('liquidity_rating', '')

        if liquidity_rating == 'EXCELLENT':
            score += 3
        elif liquidity_rating == 'GOOD':
            score += 2
        elif liquidity_rating == 'MODERATE':
            score += 1
        elif liquidity_rating == 'LOW':
            score -= 2

        # Options availability (+1 if available)
        options_data = analysis.get('options_activity', {})
        if options_data.get('options_available'):
            score += 1

        # Collect all flags
        all_red_flags = []
        all_green_flags = []
        all_warnings = []

        for category in ['float_analysis', 'short_interest', 'liquidity', 'options_activity']:
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
    """Test the analyzer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python market_structure_analyzer.py <TICKER>")
        print("\nExample: python market_structure_analyzer.py NVDA")
        return

    ticker = sys.argv[1].upper()

    analyzer = MarketStructureAnalyzer()
    result = analyzer.analyze(ticker)

    # Display results
    print(f"\n{'='*80}")
    print(f"MARKET STRUCTURE ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    print(f"Overall Score: {result['score']}/10\n")

    # Float Analysis
    if 'float_analysis' in result:
        float_data = result['float_analysis']
        print("FLOAT STRUCTURE:")
        if float_data.get('shares_outstanding_formatted'):
            print(f"  Shares Outstanding: {float_data['shares_outstanding_formatted']}")
        if float_data.get('float_shares_formatted'):
            print(f"  Float Shares: {float_data['float_shares_formatted']}")
        if float_data.get('float_pct') is not None:
            print(f"  Float %: {float_data['float_pct']:.2f}%")
        if float_data.get('tradeable_float_pct') is not None:
            print(f"  Tradeable Float %: {float_data['tradeable_float_pct']:.2f}%")
        if float_data.get('note'):
            print(f"  Note: {float_data['note']}")

    # Short Interest
    if 'short_interest' in result:
        short_data = result['short_interest']
        print(f"\nSHORT INTEREST:")
        if short_data.get('short_percent_float') is not None:
            print(f"  Short % of Float: {short_data['short_percent_float']:.2f}%")
        if short_data.get('days_to_cover'):
            print(f"  Days to Cover: {short_data['days_to_cover']:.1f}")
        if short_data.get('interpretation'):
            print(f"  Interpretation: {short_data['interpretation']}")
        if short_data.get('squeeze_risk'):
            print(f"  Squeeze Risk: {short_data['squeeze_risk']}")

    # Liquidity
    if 'liquidity' in result:
        liq_data = result['liquidity']
        print(f"\nLIQUIDITY:")
        if liq_data.get('avg_volume_formatted'):
            print(f"  Average Volume: {liq_data['avg_volume_formatted']}")
        if liq_data.get('liquidity_rating'):
            print(f"  Liquidity Rating: {liq_data['liquidity_rating']}")
        if liq_data.get('volume_to_mcap_ratio'):
            print(f"  Daily Turnover: {liq_data['volume_to_mcap_ratio']:.4f}% of market cap")

    # Options
    if 'options_activity' in result:
        opt_data = result['options_activity']
        print(f"\nOPTIONS:")
        print(f"  Options Available: {opt_data.get('options_available', False)}")
        if opt_data.get('expiration_dates_count'):
            print(f"  Expiration Dates: {opt_data['expiration_dates_count']}")

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
