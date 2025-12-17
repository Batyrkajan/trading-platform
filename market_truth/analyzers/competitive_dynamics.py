"""
Layer 6: Competitive Dynamics
Understanding the battlefield - is this company winning or losing?

Analyzes:
1. Market Position - Size relative to industry
2. Competitive Performance - Growing faster than peers?
3. Industry Health - Is the whole sector growing or dying?
4. Market Share Trends - Taking share or losing it?

Key Questions:
- Is the TAM (Total Addressable Market) real and growing?
- Is the company gaining or losing market share?
- How does it compare to key competitors?
- Is the industry consolidating or fragmenting?

Green Flags:
- Market leader in growing industry
- Taking market share from competitors
- Better margins than peers (pricing power)
- Industry tailwinds (growing TAM)

Red Flags:
- Losing market share
- Industry in structural decline
- Commoditized product (no differentiation)
- New competitors with better tech
"""
from src.yfinance_helper import yf_helper
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

try:
    from shared.data.api_tracker import api_tracker
    HAS_TRACKER = True
except:
    HAS_TRACKER = False


class CompetitiveDynamicsAnalyzer:
    """
    Analyze competitive position and industry dynamics

    Philosophy: It's easier to swim downstream (growing industry)
    than upstream (declining industry)
    """

    def __init__(self, api_manager=None):
        self.api_manager = api_manager

        # Industry classification and typical competitors
        # In production, would use proper industry databases
        self.known_competitors = {
            # Tech
            'AAPL': ['MSFT', 'GOOGL', 'AMZN', 'META'],
            'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'ORCL'],
            'GOOGL': ['MSFT', 'AMZN', 'META', 'AAPL'],
            'META': ['GOOGL', 'SNAP', 'PINS', 'TWTR'],
            'AMZN': ['MSFT', 'GOOGL', 'WMT', 'SHOP'],

            # Semiconductors
            'NVDA': ['AMD', 'INTC', 'QCOM', 'AVGO'],
            'AMD': ['NVDA', 'INTC', 'QCOM'],
            'INTC': ['AMD', 'NVDA', 'QCOM'],

            # Auto/EV
            'TSLA': ['F', 'GM', 'RIVN', 'LCID'],
            'F': ['GM', 'TSLA', 'TM'],
            'GM': ['F', 'TSLA', 'TM'],

            # Retail
            'WMT': ['TGT', 'COST', 'AMZN'],
            'TGT': ['WMT', 'COST'],
            'COST': ['WMT', 'TGT'],

            # Social/Gaming
            'GME': ['BBBY', 'CHWY'],
        }

    def analyze(self, ticker: str) -> Dict:
        """
        Complete competitive dynamics analysis

        Returns comprehensive analysis with score 0-10
        """
        print(f"\n{'='*80}")
        print(f"COMPETITIVE DYNAMICS ANALYSIS: {ticker}")
        print(f"{'='*80}\n")

        try:
            stock = yf_helper.get_ticker(ticker)
            info = stock.info

            analysis = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'score': 0,
                'market_position': {},
                'competitive_performance': {},
                'industry_health': {},
                'relative_strength': {},
                'red_flags': [],
                'green_flags': [],
                'warnings': []
            }

            # 1. Market Position Analysis
            print("Analyzing market position...")
            position = self.analyze_market_position(stock, info, ticker)
            analysis['market_position'] = position

            # 2. Competitive Performance
            print("Analyzing competitive performance...")
            performance = self.analyze_competitive_performance(stock, info, ticker)
            analysis['competitive_performance'] = performance

            # 3. Industry Health
            print("Analyzing industry health...")
            industry = self.analyze_industry_health(stock, info, ticker)
            analysis['industry_health'] = industry

            # 4. Relative Strength vs Peers
            print("Analyzing relative strength vs peers...")
            relative = self.analyze_relative_strength(stock, info, ticker)
            analysis['relative_strength'] = relative

            # Calculate score
            score = self._calculate_score(analysis)
            analysis['score'] = score

            print(f"\nCompetitive Dynamics Score: {score}/10")

            return analysis

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return {
                'ticker': ticker,
                'score': 0,
                'error': str(e),
                'red_flags': ['ANALYSIS_FAILED']
            }

    def analyze_market_position(self, stock, info: Dict, ticker: str) -> Dict:
        """
        Analyze company's position in its market

        Metrics:
        - Market cap ranking (leader vs follower)
        - Industry category
        - Scale advantages
        """
        analysis = {
            'market_cap': None,
            'industry': None,
            'sector': None,
            'position_rating': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            market_cap = info.get('marketCap')
            industry = info.get('industry', 'Unknown')
            sector = info.get('sector', 'Unknown')

            analysis['market_cap'] = market_cap
            analysis['industry'] = industry
            analysis['sector'] = sector

            if market_cap:
                analysis['market_cap_formatted'] = f"${market_cap / 1e9:.1f}B"

                # Position based on size
                if market_cap > 500e9:  # $500B+
                    analysis['position_rating'] = 'MEGA_CAP_LEADER'
                    analysis['green_flags'].append('MARKET_LEADER')
                elif market_cap > 100e9:  # $100B+
                    analysis['position_rating'] = 'LARGE_CAP_LEADER'
                    analysis['green_flags'].append('STRONG_POSITION')
                elif market_cap > 10e9:  # $10B+
                    analysis['position_rating'] = 'MID_CAP_COMPETITOR'
                elif market_cap > 2e9:  # $2B+
                    analysis['position_rating'] = 'SMALL_CAP_NICHE'
                else:
                    analysis['position_rating'] = 'MICRO_CAP_STARTUP'
                    analysis['warnings'] = ['SMALL_MARKET_CAP']

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_competitive_performance(self, stock, info: Dict, ticker: str) -> Dict:
        """
        Analyze performance vs competitors

        Key Metrics:
        - Revenue growth vs peers
        - Margin superiority
        - Market share trends (proxy)
        """
        analysis = {
            'revenue_growth': None,
            'margin_advantage': None,
            'peers': [],
            'red_flags': [],
            'green_flags': []
        }

        try:
            # Get competitors
            competitors = self.known_competitors.get(ticker, [])
            analysis['peers'] = competitors

            if not competitors:
                analysis['note'] = 'No peer comparison data available'
                return analysis

            # Check API quota before fetching peer data
            skip_peers = False
            if HAS_TRACKER:
                quota_remaining = api_tracker.get_quota_remaining()
                if quota_remaining < 20:  # Reserve 20 calls
                    print(f"  [QUOTA LOW] Skipping peer analysis (only {quota_remaining} calls remaining)")
                    analysis['note'] = f'Peer analysis skipped (API quota low: {quota_remaining}/250 remaining)'
                    skip_peers = True

            # Compare metrics
            own_revenue_growth = info.get('revenueGrowth', 0)
            own_margin = info.get('operatingMargins', 0)

            analysis['revenue_growth'] = round(own_revenue_growth * 100, 2) if own_revenue_growth else None
            analysis['operating_margin'] = round(own_margin * 100, 2) if own_margin else None

            if skip_peers:
                return analysis

            # Get peer data
            peer_growths = []
            peer_margins = []

            for peer_ticker in competitors[:3]:  # Limit to 3 peers to avoid rate limits
                try:
                    peer = yf_helper.get_ticker(peer_ticker)
                    peer_info = peer.info

                    peer_growth = peer_info.get('revenueGrowth', 0)
                    peer_margin = peer_info.get('operatingMargins', 0)

                    if peer_growth:
                        peer_growths.append(peer_growth)
                    if peer_margin:
                        peer_margins.append(peer_margin)
                except:
                    continue

            # Compare
            if peer_growths and own_revenue_growth:
                avg_peer_growth = np.mean(peer_growths)
                analysis['peer_avg_growth'] = round(avg_peer_growth * 100, 2)

                if own_revenue_growth > avg_peer_growth * 1.2:  # Growing 20% faster
                    analysis['green_flags'].append('OUTGROWING_PEERS')
                    analysis['growth_vs_peers'] = 'SUPERIOR'
                elif own_revenue_growth > avg_peer_growth:
                    analysis['growth_vs_peers'] = 'BETTER'
                elif own_revenue_growth > avg_peer_growth * 0.8:
                    analysis['growth_vs_peers'] = 'SIMILAR'
                else:
                    analysis['red_flags'].append('UNDERPERFORMING_PEERS')
                    analysis['growth_vs_peers'] = 'LAGGING'

            if peer_margins and own_margin:
                avg_peer_margin = np.mean(peer_margins)
                analysis['peer_avg_margin'] = round(avg_peer_margin * 100, 2)

                if own_margin > avg_peer_margin * 1.2:  # 20% better margins
                    analysis['green_flags'].append('MARGIN_LEADERSHIP')
                    analysis['margin_vs_peers'] = 'SUPERIOR'
                elif own_margin > avg_peer_margin:
                    analysis['margin_vs_peers'] = 'BETTER'
                else:
                    analysis['margin_vs_peers'] = 'LAGGING'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_industry_health(self, stock, info: Dict, ticker: str) -> Dict:
        """
        Analyze overall industry health

        Is the tide rising or falling?

        Proxies:
        - Sector growth trends
        - Industry maturity
        - Disruption risk
        """
        analysis = {
            'sector': None,
            'industry': None,
            'health_rating': None,
            'red_flags': [],
            'green_flags': []
        }

        try:
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')

            analysis['sector'] = sector
            analysis['industry'] = industry

            # Industry health heuristics
            # In production, would use proper industry research databases

            # Growth industries
            growth_keywords = [
                'Technology', 'Software', 'Cloud', 'AI', 'Semiconductor',
                'Renewable', 'Electric', 'Biotech', 'Internet', 'E-commerce'
            ]

            # Declining industries
            decline_keywords = [
                'Coal', 'Print', 'Department Store', 'Brick & Mortar',
                'Traditional Media', 'Cable', 'Newspaper'
            ]

            industry_str = f"{sector} {industry}".lower()

            # Check for growth signals
            for keyword in growth_keywords:
                if keyword.lower() in industry_str:
                    analysis['health_rating'] = 'GROWING'
                    analysis['green_flags'].append('GROWTH_INDUSTRY')
                    break

            # Check for decline signals
            for keyword in decline_keywords:
                if keyword.lower() in industry_str:
                    analysis['health_rating'] = 'DECLINING'
                    analysis['red_flags'].append('DECLINING_INDUSTRY')
                    break

            # Default to stable if no signals
            if not analysis['health_rating']:
                analysis['health_rating'] = 'MATURE_STABLE'

            # Specific industry insights
            if 'retail' in industry_str and 'e-commerce' not in industry_str:
                analysis['warnings'] = ['RETAIL_DISRUPTION_RISK']

            if 'automotive' in industry_str or 'auto manufacturer' in industry_str:
                analysis['note'] = 'Auto industry transitioning to EV - mixed outlook'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_relative_strength(self, stock, info: Dict, ticker: str) -> Dict:
        """
        Analyze relative competitive strength

        Combines multiple factors:
        - Brand power (margins)
        - Innovation (R&D)
        - Efficiency (ROE, ROA)
        - Market sentiment
        """
        analysis = {
            'strength_score': 0,
            'competitive_advantages': [],
            'competitive_weaknesses': [],
            'red_flags': [],
            'green_flags': []
        }

        try:
            strengths = []
            weaknesses = []

            # Brand power (margin proxy)
            gross_margin = info.get('grossMargins', 0)
            if gross_margin > 0.60:  # 60%+
                strengths.append('STRONG_BRAND_PRICING_POWER')
                analysis['green_flags'].append('PRICING_POWER')
            elif gross_margin < 0.20:  # <20%
                weaknesses.append('LOW_MARGINS_COMMODITY')
                analysis['red_flags'].append('COMMODITIZED_PRODUCT')

            # Innovation proxy (if available)
            # Would need R&D data from financials for full analysis

            # Efficiency
            roe = info.get('returnOnEquity', 0)
            if roe and roe > 0.20:  # 20%+
                strengths.append('EFFICIENT_CAPITAL_ALLOCATION')
                analysis['green_flags'].append('HIGH_ROE')
            elif roe and roe < 0.10:  # <10%
                weaknesses.append('POOR_CAPITAL_EFFICIENCY')

            # Growth momentum
            revenue_growth = info.get('revenueGrowth', 0)
            if revenue_growth and revenue_growth > 0.20:  # 20%+
                strengths.append('STRONG_GROWTH_MOMENTUM')
            elif revenue_growth and revenue_growth < 0:  # Declining
                weaknesses.append('NEGATIVE_GROWTH')
                analysis['red_flags'].append('SHRINKING_BUSINESS')

            analysis['competitive_advantages'] = strengths
            analysis['competitive_weaknesses'] = weaknesses

            # Calculate strength score
            strength_score = len(strengths) - len(weaknesses)
            analysis['strength_score'] = strength_score

            if strength_score >= 3:
                analysis['overall_rating'] = 'DOMINANT'
            elif strength_score >= 1:
                analysis['overall_rating'] = 'COMPETITIVE'
            elif strength_score >= -1:
                analysis['overall_rating'] = 'CHALLENGED'
            else:
                analysis['overall_rating'] = 'WEAK'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _calculate_score(self, analysis: Dict) -> int:
        """
        Calculate overall competitive dynamics score (0-10)

        Weighting:
        - Market position: 0-2 points
        - Competitive performance: 0-3 points
        - Industry health: 0-2 points
        - Relative strength: 0-3 points
        """
        score = 5  # Start neutral

        # Market Position (0-2 points)
        position = analysis.get('market_position', {})
        position_rating = position.get('position_rating', '')

        if position_rating in ['MEGA_CAP_LEADER', 'LARGE_CAP_LEADER']:
            score += 2
        elif position_rating == 'MID_CAP_COMPETITOR':
            score += 1
        elif position_rating == 'MICRO_CAP_STARTUP':
            score -= 1

        # Competitive Performance (0-3 points)
        performance = analysis.get('competitive_performance', {})
        growth_vs_peers = performance.get('growth_vs_peers', '')
        margin_vs_peers = performance.get('margin_vs_peers', '')

        if growth_vs_peers == 'SUPERIOR':
            score += 2
        elif growth_vs_peers == 'BETTER':
            score += 1
        elif growth_vs_peers == 'LAGGING':
            score -= 1

        if margin_vs_peers == 'SUPERIOR':
            score += 1

        # Industry Health (0-2 points)
        industry = analysis.get('industry_health', {})
        health_rating = industry.get('health_rating', '')

        if health_rating == 'GROWING':
            score += 2
        elif health_rating == 'MATURE_STABLE':
            score += 0
        elif health_rating == 'DECLINING':
            score -= 2

        # Relative Strength (0-3 points)
        relative = analysis.get('relative_strength', {})
        strength_score = relative.get('strength_score', 0)

        score += min(3, max(-3, strength_score))

        # Collect all flags
        all_red_flags = []
        all_green_flags = []
        all_warnings = []

        for category in ['market_position', 'competitive_performance', 'industry_health', 'relative_strength']:
            if category in analysis:
                cat_data = analysis[category]
                if isinstance(cat_data, dict):
                    all_red_flags.extend(cat_data.get('red_flags', []))
                    all_green_flags.extend(cat_data.get('green_flags', []))
                    all_warnings.extend(cat_data.get('warnings', []))

        analysis['red_flags'] = list(set(all_red_flags))
        analysis['green_flags'] = list(set(all_green_flags))
        analysis['warnings'] = list(set(all_warnings))

        # Bonus/penalty for critical flags
        if 'DECLINING_INDUSTRY' in all_red_flags:
            score -= 2
        if 'GROWTH_INDUSTRY' in all_green_flags:
            score += 1

        # Cap at 0-10
        return max(0, min(10, score))


def main():
    """Test the analyzer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python competitive_dynamics_analyzer.py <TICKER>")
        print("\nExample: python competitive_dynamics_analyzer.py NVDA")
        return

    ticker = sys.argv[1].upper()

    analyzer = CompetitiveDynamicsAnalyzer()
    result = analyzer.analyze(ticker)

    # Display results
    print(f"\n{'='*80}")
    print(f"COMPETITIVE DYNAMICS ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    print(f"Overall Score: {result['score']}/10\n")

    # Market Position
    if 'market_position' in result:
        pos = result['market_position']
        print("MARKET POSITION:")
        if pos.get('market_cap_formatted'):
            print(f"  Market Cap: {pos['market_cap_formatted']}")
        if pos.get('sector'):
            print(f"  Sector: {pos['sector']}")
        if pos.get('industry'):
            print(f"  Industry: {pos['industry']}")
        if pos.get('position_rating'):
            print(f"  Position: {pos['position_rating']}")

    # Competitive Performance
    if 'competitive_performance' in result:
        perf = result['competitive_performance']
        print(f"\nCOMPETITIVE PERFORMANCE:")
        if perf.get('peers'):
            print(f"  Key Competitors: {', '.join(perf['peers'])}")
        if perf.get('revenue_growth') is not None:
            print(f"  Revenue Growth: {perf['revenue_growth']:.2f}%")
        if perf.get('peer_avg_growth') is not None:
            print(f"  Peer Avg Growth: {perf['peer_avg_growth']:.2f}%")
        if perf.get('growth_vs_peers'):
            print(f"  Growth vs Peers: {perf['growth_vs_peers']}")
        if perf.get('operating_margin') is not None:
            print(f"  Operating Margin: {perf['operating_margin']:.2f}%")
        if perf.get('peer_avg_margin') is not None:
            print(f"  Peer Avg Margin: {perf['peer_avg_margin']:.2f}%")
        if perf.get('margin_vs_peers'):
            print(f"  Margin vs Peers: {perf['margin_vs_peers']}")

    # Industry Health
    if 'industry_health' in result:
        ind = result['industry_health']
        print(f"\nINDUSTRY HEALTH:")
        if ind.get('health_rating'):
            print(f"  Health Rating: {ind['health_rating']}")
        if ind.get('note'):
            print(f"  Note: {ind['note']}")

    # Relative Strength
    if 'relative_strength' in result:
        rel = result['relative_strength']
        print(f"\nRELATIVE STRENGTH:")
        if rel.get('overall_rating'):
            print(f"  Overall Rating: {rel['overall_rating']}")
        if rel.get('strength_score') is not None:
            print(f"  Strength Score: {rel['strength_score']}")
        if rel.get('competitive_advantages'):
            print(f"  Advantages:")
            for adv in rel['competitive_advantages']:
                print(f"    + {adv}")
        if rel.get('competitive_weaknesses'):
            print(f"  Weaknesses:")
            for weak in rel['competitive_weaknesses']:
                print(f"    - {weak}")

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
