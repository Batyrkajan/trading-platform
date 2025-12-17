"""
Layer 2: Business Model Forensics
Understanding the money machine

Analyzes:
1. Revenue Architecture - How does this company ACTUALLY make money?
2. Unit Economics - Does each transaction actually make money?
3. The Moat Test - What stops competitors from eating their lunch?

Framework from market_truth_framework.md - Building systematically
"""
from src.yfinance_helper import yf_helper
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional


class BusinessModelAnalyzer:
    """
    Deep dive into how the company makes money

    Philosophy: Don't trust what they SAY - analyze what they DO
    """

    def __init__(self, api_manager=None):
        self.api_manager = api_manager

    def analyze(self, ticker: str) -> Dict:
        """
        Complete business model analysis

        Returns comprehensive analysis with score 0-10
        """
        print(f"\n{'='*80}")
        print(f"BUSINESS MODEL FORENSICS: {ticker}")
        print(f"{'='*80}\n")

        try:
            # Use API manager if available
            if self.api_manager:
                stock_data = self.api_manager.get_stock_data(ticker)
                stock = stock_data['data']
                # Handle FMP vs yfinance data
                if stock_data['source'] == 'FMP':
                    info = stock  # FMP returns profile dict directly
                else:
                    info = stock.info
            else:
                stock = yf_helper.get_ticker(ticker)
                info = stock.info

            analysis = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'score': 0,
                'revenue_architecture': {},
                'unit_economics': {},
                'moat_analysis': {},
                'red_flags': [],
                'green_flags': [],
                'warnings': []
            }

            # 1. Revenue Architecture
            print("Analyzing revenue architecture...")
            revenue_arch = self.analyze_revenue_architecture(stock, info)
            analysis['revenue_architecture'] = revenue_arch

            # 2. Unit Economics (limited by public data)
            print("Analyzing unit economics...")
            unit_econ = self.analyze_unit_economics(stock, info)
            analysis['unit_economics'] = unit_econ

            # 3. Moat Analysis
            print("Analyzing competitive moat...")
            moat = self.analyze_moat(stock, info)
            analysis['moat_analysis'] = moat

            # Calculate score
            score = self._calculate_score(analysis)
            analysis['score'] = score

            print(f"\nBusiness Model Score: {score}/10")

            return analysis

        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            return {
                'ticker': ticker,
                'score': 0,
                'error': str(e),
                'red_flags': ['ANALYSIS_FAILED']
            }

    def analyze_revenue_architecture(self, stock, info: Dict) -> Dict:
        """
        Understand how they make money

        Key Questions:
        - Is revenue growing or declining?
        - What are the margins? (High margin = pricing power/moat)
        - Is it recurring or one-time?
        - Geographic/segment concentration?

        Red Flags:
        - Declining revenue
        - Margins compressing
        - High concentration risk
        """
        analysis = {
            'revenue_quality': {},
            'margins': {},
            'growth': {},
            'red_flags': [],
            'green_flags': []
        }

        try:
            # Get financial statements
            financials = stock.financials

            if financials is None or financials.empty:
                analysis['warnings'] = ['No financial data available']
                return analysis

            # Revenue Analysis
            if 'Total Revenue' in financials.index:
                revenues = financials.loc['Total Revenue']

                # Growth rate (YoY or latest vs previous)
                if len(revenues) >= 2:
                    latest_rev = revenues.iloc[0]
                    previous_rev = revenues.iloc[1]

                    if pd.notna(latest_rev) and pd.notna(previous_rev) and previous_rev != 0:
                        revenue_growth = ((latest_rev - previous_rev) / previous_rev) * 100

                        analysis['growth']['revenue_growth_pct'] = round(revenue_growth, 2)
                        analysis['growth']['latest_revenue'] = latest_rev
                        analysis['growth']['previous_revenue'] = previous_rev

                        # Flags
                        if revenue_growth > 20:
                            analysis['green_flags'].append('STRONG_REVENUE_GROWTH')
                        elif revenue_growth > 10:
                            analysis['green_flags'].append('HEALTHY_REVENUE_GROWTH')
                        elif revenue_growth < 0:
                            analysis['red_flags'].append('DECLINING_REVENUE')
                        elif revenue_growth < 5:
                            analysis['red_flags'].append('SLOWING_GROWTH')

                # Multi-year trend
                if len(revenues) >= 3:
                    growth_rates = []
                    for i in range(len(revenues) - 1):
                        curr = revenues.iloc[i]
                        prev = revenues.iloc[i + 1]
                        if pd.notna(curr) and pd.notna(prev) and prev != 0:
                            growth_rate = ((curr - prev) / prev) * 100
                            growth_rates.append(growth_rate)

                    if growth_rates:
                        avg_growth = np.mean(growth_rates)
                        analysis['growth']['avg_growth_3yr'] = round(avg_growth, 2)

                        # Check if growth is accelerating or decelerating
                        if len(growth_rates) >= 2:
                            if growth_rates[0] > growth_rates[1]:
                                analysis['green_flags'].append('GROWTH_ACCELERATING')
                            elif growth_rates[0] < growth_rates[1] and growth_rates[0] > 0:
                                analysis['warnings'] = analysis.get('warnings', []) + ['GROWTH_DECELERATING']

            # Margin Analysis
            gross_margin = info.get('grossMargins')
            operating_margin = info.get('operatingMargins')
            profit_margin = info.get('profitMargins')

            analysis['margins'] = {
                'gross_margin': round(gross_margin * 100, 2) if gross_margin else None,
                'operating_margin': round(operating_margin * 100, 2) if operating_margin else None,
                'profit_margin': round(profit_margin * 100, 2) if profit_margin else None
            }

            # Margin quality flags
            if gross_margin:
                if gross_margin > 0.70:  # 70%+ = Software/SaaS pricing power
                    analysis['green_flags'].append('EXCEPTIONAL_MARGINS')
                elif gross_margin > 0.50:  # 50%+ = Strong pricing power
                    analysis['green_flags'].append('STRONG_MARGINS')
                elif gross_margin < 0.20:  # <20% = Commodity/low moat
                    analysis['red_flags'].append('LOW_MARGINS')

            # Check margin trends (if we have historical data)
            # Would need quarterly data for this

            # Revenue Quality Metrics
            analysis['revenue_quality'] = {
                'revenue_per_share': info.get('revenuePerShare'),
                'total_revenue': info.get('totalRevenue'),
                'revenue_growth_yoy': info.get('revenueGrowth')
            }

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_unit_economics(self, stock, info: Dict) -> Dict:
        """
        Does each transaction make money?

        True CAC/LTV analysis requires:
        - Customer count (rarely disclosed)
        - Churn rate (rarely disclosed)
        - S&M spend per new customer

        What we CAN measure from public data:
        - Sales efficiency: Revenue per $ of S&M spend
        - R&D efficiency: Revenue per $ of R&D spend
        - Operating leverage: Revenue growth vs opex growth
        """
        analysis = {
            'efficiency_metrics': {},
            'operating_leverage': {},
            'note': 'Full unit economics require customer-level data not available publicly'
        }

        try:
            # Get financials
            financials = stock.financials

            if financials is None or financials.empty:
                return {'note': 'No financial data available'}

            # Calculate sales efficiency (if S&M data available)
            # This is a proxy for CAC efficiency

            # Get operating expenses
            if 'Selling General Administrative' in financials.index:
                sga = financials.loc['Selling General Administrative']
            elif 'Selling General And Administrative' in financials.index:
                sga = financials.loc['Selling General And Administrative']
            else:
                sga = None

            if 'Research Development' in financials.index:
                rd = financials.loc['Research Development']
            elif 'Research And Development' in financials.index:
                rd = financials.loc['Research And Development']
            else:
                rd = None

            if 'Total Revenue' in financials.index:
                revenue = financials.loc['Total Revenue']
            else:
                revenue = None

            # Sales & Marketing Efficiency
            if sga is not None and revenue is not None and len(revenue) >= 1:
                latest_revenue = revenue.iloc[0]
                latest_sga = sga.iloc[0] if sga is not None else None

                if latest_sga and pd.notna(latest_revenue) and pd.notna(latest_sga) and latest_sga != 0:
                    sales_efficiency = latest_revenue / abs(latest_sga)
                    analysis['efficiency_metrics']['revenue_per_sga_dollar'] = round(sales_efficiency, 2)

                    # Interpretation
                    if sales_efficiency > 3:  # $3+ revenue per $1 S&M
                        analysis['efficiency_metrics']['sales_efficiency'] = 'EFFICIENT'
                    elif sales_efficiency > 1.5:
                        analysis['efficiency_metrics']['sales_efficiency'] = 'MODERATE'
                    else:
                        analysis['efficiency_metrics']['sales_efficiency'] = 'INEFFICIENT'

            # R&D Efficiency
            if rd is not None and revenue is not None and len(revenue) >= 1:
                latest_revenue = revenue.iloc[0]
                latest_rd = rd.iloc[0] if rd is not None else None

                if latest_rd and pd.notna(latest_revenue) and pd.notna(latest_rd) and latest_rd != 0:
                    rd_efficiency = latest_revenue / abs(latest_rd)
                    analysis['efficiency_metrics']['revenue_per_rd_dollar'] = round(rd_efficiency, 2)

                    # R&D as % of revenue
                    rd_pct = (abs(latest_rd) / latest_revenue) * 100
                    analysis['efficiency_metrics']['rd_pct_of_revenue'] = round(rd_pct, 2)

            # Operating Leverage Analysis
            # Compare revenue growth vs operating expense growth
            if revenue is not None and len(revenue) >= 2:
                latest_rev = revenue.iloc[0]
                prev_rev = revenue.iloc[1]

                if 'Operating Expense' in financials.index:
                    opex = financials.loc['Operating Expense']
                    if len(opex) >= 2:
                        latest_opex = opex.iloc[0]
                        prev_opex = opex.iloc[1]

                        if pd.notna(latest_rev) and pd.notna(prev_rev) and prev_rev != 0:
                            rev_growth = ((latest_rev - prev_rev) / prev_rev) * 100

                            if pd.notna(latest_opex) and pd.notna(prev_opex) and prev_opex != 0:
                                opex_growth = ((latest_opex - prev_opex) / prev_opex) * 100

                                analysis['operating_leverage'] = {
                                    'revenue_growth': round(rev_growth, 2),
                                    'opex_growth': round(opex_growth, 2),
                                    'leverage_ratio': round(rev_growth - opex_growth, 2)
                                }

                                # Positive operating leverage = revenue growing faster than costs
                                if rev_growth > opex_growth and rev_growth > 0:
                                    analysis['operating_leverage']['verdict'] = 'POSITIVE_LEVERAGE'
                                else:
                                    analysis['operating_leverage']['verdict'] = 'NEGATIVE_LEVERAGE'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_moat(self, stock, info: Dict) -> Dict:
        """
        What stops competitors from eating their lunch?

        6 Types of Moats:
        1. Network Effects - Product gets better with more users
        2. Switching Costs - How painful to leave?
        3. Data Advantage - Unique data competitors can't get?
        4. Brand Power - Would customers pay premium?
        5. Cost Advantage - Can produce cheaper than anyone?
        6. Regulatory Barriers - Does regulation protect them?

        Scoring: Each strong moat = 1 point
        - 0-1: Commodity (avoid)
        - 2-3: Competitive advantage
        - 4+: Monopoly/oligopoly (best)
        """
        analysis = {
            'moat_count': 0,
            'moats': {},
            'moat_score': 0,
            'verdict': ''
        }

        try:
            # 1. Brand Power Proxy: Profit Margins
            # High margins = pricing power = brand strength
            gross_margin = info.get('grossMargins', 0)
            profit_margin = info.get('profitMargins', 0)

            brand_score = 0
            if gross_margin > 0.60:  # 60%+ = strong brand
                brand_score = 2
                analysis['moats']['brand_power'] = 'STRONG'
            elif gross_margin > 0.40:
                brand_score = 1
                analysis['moats']['brand_power'] = 'MODERATE'
            else:
                analysis['moats']['brand_power'] = 'WEAK'

            # 2. Market Position: Market cap relative to industry
            market_cap = info.get('marketCap', 0)

            if market_cap > 500e9:  # $500B+ = dominant position
                market_score = 2
                analysis['moats']['market_position'] = 'DOMINANT'
            elif market_cap > 100e9:  # $100B+ = strong
                market_score = 1
                analysis['moats']['market_position'] = 'STRONG'
            elif market_cap > 10e9:  # $10B+ = competitive
                market_score = 1
                analysis['moats']['market_position'] = 'COMPETITIVE'
            else:
                market_score = 0
                analysis['moats']['market_position'] = 'SMALL'

            # 3. Cost Advantage Proxy: Return on Assets
            # High ROA = efficient asset utilization = potential cost advantage
            roa = info.get('returnOnAssets', 0)

            if roa and roa > 0.15:  # 15%+ ROA = very efficient
                cost_score = 1
                analysis['moats']['cost_advantage'] = 'LIKELY'
            else:
                cost_score = 0
                analysis['moats']['cost_advantage'] = 'UNCLEAR'

            # 4. Switching Costs Proxy: Check industry and business type
            # Software/SaaS = high switching costs
            # Retail/commodity = low switching costs
            industry = info.get('industry', '')
            sector = info.get('sector', '')

            switching_score = 0
            if 'Software' in industry or 'SaaS' in industry or sector == 'Technology':
                # Software often has high switching costs (integrations, training, data)
                switching_score = 1
                analysis['moats']['switching_costs'] = 'LIKELY_HIGH'
            elif 'Healthcare' in sector or 'Financial' in sector:
                # Regulatory/compliance creates switching costs
                switching_score = 1
                analysis['moats']['switching_costs'] = 'REGULATORY'
            else:
                analysis['moats']['switching_costs'] = 'UNCLEAR'

            # 5. Network Effects: Hard to measure, industry-specific
            # Social media, marketplaces, payments = network effects
            if 'Social' in industry or 'Internet' in industry or 'Marketplace' in industry:
                network_score = 1
                analysis['moats']['network_effects'] = 'LIKELY'
            else:
                network_score = 0
                analysis['moats']['network_effects'] = 'UNCLEAR'

            # Calculate total moat score
            total_moat_score = brand_score + market_score + cost_score + switching_score + network_score

            analysis['moat_score'] = total_moat_score
            analysis['moat_count'] = total_moat_score

            # Verdict
            if total_moat_score >= 4:
                analysis['verdict'] = 'STRONG_MOAT'
            elif total_moat_score >= 2:
                analysis['verdict'] = 'MODERATE_MOAT'
            else:
                analysis['verdict'] = 'WEAK_MOAT'

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _calculate_score(self, analysis: Dict) -> int:
        """
        Calculate overall business model score (0-10)

        Weighting:
        - Revenue quality: 0-3 points
        - Margins: 0-2 points
        - Moat strength: 0-5 points
        """
        score = 0

        # Revenue Quality (0-3)
        rev_arch = analysis.get('revenue_architecture', {})
        growth = rev_arch.get('growth', {})

        revenue_growth = growth.get('revenue_growth_pct', 0)
        if revenue_growth > 20:
            score += 3
        elif revenue_growth > 10:
            score += 2
        elif revenue_growth > 0:
            score += 1
        elif revenue_growth < 0:
            score -= 1  # Penalty for decline

        # Margins (0-2)
        margins = rev_arch.get('margins', {})
        gross_margin = margins.get('gross_margin', 0)

        if gross_margin:
            if gross_margin > 60:
                score += 2
            elif gross_margin > 40:
                score += 1

        # Moat (0-5)
        moat = analysis.get('moat_analysis', {})
        moat_score = moat.get('moat_score', 0)
        score += min(moat_score, 5)

        # Collect all flags
        all_red_flags = []
        all_green_flags = []

        for category in ['revenue_architecture', 'unit_economics', 'moat_analysis']:
            if category in analysis:
                cat_data = analysis[category]
                if isinstance(cat_data, dict):
                    all_red_flags.extend(cat_data.get('red_flags', []))
                    all_green_flags.extend(cat_data.get('green_flags', []))

        analysis['red_flags'] = list(set(all_red_flags))
        analysis['green_flags'] = list(set(all_green_flags))

        # Cap at 0-10
        return max(0, min(10, score))


def main():
    """Test the analyzer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python business_model_analyzer.py <TICKER>")
        print("\nExample: python business_model_analyzer.py AAPL")
        return

    ticker = sys.argv[1].upper()

    analyzer = BusinessModelAnalyzer()
    result = analyzer.analyze(ticker)

    # Display results
    print(f"\n{'='*80}")
    print(f"BUSINESS MODEL ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    print(f"Overall Score: {result['score']}/10\n")

    # Revenue Architecture
    if 'revenue_architecture' in result:
        rev = result['revenue_architecture']

        if 'growth' in rev:
            print("REVENUE GROWTH:")
            growth = rev['growth']
            if 'revenue_growth_pct' in growth:
                print(f"  YoY Growth: {growth['revenue_growth_pct']:+.1f}%")
            if 'avg_growth_3yr' in growth:
                print(f"  3-Year Avg: {growth['avg_growth_3yr']:+.1f}%")

        if 'margins' in rev:
            print(f"\nMARGINS:")
            margins = rev['margins']
            if margins.get('gross_margin'):
                print(f"  Gross Margin: {margins['gross_margin']:.1f}%")
            if margins.get('operating_margin'):
                print(f"  Operating Margin: {margins['operating_margin']:.1f}%")
            if margins.get('profit_margin'):
                print(f"  Profit Margin: {margins['profit_margin']:.1f}%")

    # Moat Analysis
    if 'moat_analysis' in result:
        moat = result['moat_analysis']
        print(f"\nMOAT ANALYSIS:")
        print(f"  Moat Score: {moat.get('moat_score', 0)}/7")
        print(f"  Verdict: {moat.get('verdict', 'UNKNOWN')}")

        if 'moats' in moat:
            print(f"\n  Moat Breakdown:")
            for moat_type, strength in moat['moats'].items():
                print(f"    {moat_type.replace('_', ' ').title()}: {strength}")

    # Flags
    if result.get('green_flags'):
        print(f"\nGREEN FLAGS:")
        for flag in result['green_flags']:
            print(f"  + {flag}")

    if result.get('red_flags'):
        print(f"\nRED FLAGS:")
        for flag in result['red_flags']:
            print(f"  - {flag}")

    if result.get('warnings'):
        print(f"\nWARNINGS:")
        for warning in result['warnings']:
            print(f"  ! {warning}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
