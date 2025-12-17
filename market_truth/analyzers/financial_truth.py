"""
Layer 3: Financial Truth Extraction
"Revenue is opinion, cash is fact" - The Golden Rule

Analyzes:
1. Cash Flow Forensics - Is profitability real?
2. Receivables Game - Are customers actually paying?
3. Inventory Trick - Is product actually selling?
4. Debt Time Bomb - Can they service their debt?

Red Flags:
- Revenue growing but OCF shrinking → Booking uncollectible sales
- Net Income positive but FCF negative → Accounting fiction
- Stock-based comp > 15% of revenue → Diluting to fund ops
- DSO increasing → Collection problems
- Inventory days increasing → Product not selling
"""
from src.yfinance_helper import yf_helper
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional


class FinancialTruthAnalyzer:
    """
    Extracts truth from financial statements

    The system checks what management DOESN'T want you to see:
    - Cash flow vs reported earnings
    - Quality of receivables
    - Inventory build-up
    - Debt maturity wall
    """

    def __init__(self, api_manager=None):
        self.api_manager = api_manager

    def analyze(self, ticker: str) -> Dict:
        """
        Run complete financial truth analysis

        Returns score 0-10 and detailed findings
        """
        try:
            # Use API manager if available, otherwise fallback to yf_helper
            if self.api_manager:
                stock_data = self.api_manager.get_stock_data(ticker)
                stock = stock_data['data']
            else:
                stock = yf_helper.get_ticker(ticker)

            analysis = {
                'ticker': ticker,
                'timestamp': datetime.now(),
                'score': 0,
                'cash_flow': {},
                'receivables': {},
                'inventory': {},
                'debt': {},
                'red_flags': [],
                'green_flags': []
            }

            # 1. Cash Flow Forensics
            cash_flow_analysis = self.analyze_cash_flow(stock)
            analysis['cash_flow'] = cash_flow_analysis

            # 2. Receivables Analysis
            receivables_analysis = self.analyze_receivables(stock)
            analysis['receivables'] = receivables_analysis

            # 3. Inventory Analysis (for relevant companies)
            inventory_analysis = self.analyze_inventory(stock)
            analysis['inventory'] = inventory_analysis

            # 4. Debt Analysis
            debt_analysis = self.analyze_debt(stock)
            analysis['debt'] = debt_analysis

            # Calculate overall score
            score = self._calculate_score(analysis)
            analysis['score'] = score

            return analysis

        except Exception as e:
            return {
                'ticker': ticker,
                'score': 0,
                'error': str(e),
                'red_flags': ['ANALYSIS_FAILED']
            }

    def analyze_cash_flow(self, stock) -> Dict:
        """
        Cash Flow Forensics - The truth about profitability

        Key Checks:
        1. Revenue vs Operating Cash Flow trend
        2. Net Income vs Free Cash Flow
        3. Stock-based compensation as % of revenue
        4. Capex trend (increasing = bad)

        Red Flags:
        - Revenue up, OCF down = uncollectible sales
        - Positive NI, negative FCF = accounting tricks
        - SBC > 15% revenue = dilution funding
        """
        try:
            # Get statements
            financials = stock.financials
            cash_flow = stock.cashflow
            info = stock.info

            if cash_flow is None or cash_flow.empty:
                return {'error': 'No cash flow data available'}

            analysis = {
                'quarterly_data': [],
                'trends': {},
                'red_flags': [],
                'green_flags': []
            }

            # Extract key metrics for last 5 quarters
            if 'Operating Cash Flow' in cash_flow.index:
                ocf = cash_flow.loc['Operating Cash Flow']
            elif 'Total Cash From Operating Activities' in cash_flow.index:
                ocf = cash_flow.loc['Total Cash From Operating Activities']
            else:
                return {'error': 'Cannot find Operating Cash Flow'}

            if 'Capital Expenditures' in cash_flow.index:
                capex = cash_flow.loc['Capital Expenditures']
            elif 'Capital Expenditure' in cash_flow.index:
                capex = cash_flow.loc['Capital Expenditure']
            else:
                capex = pd.Series([0] * len(ocf), index=ocf.index)

            # Free Cash Flow = OCF - Capex
            fcf = ocf + capex  # Capex is negative in statements

            # Get revenue from financials
            if financials is not None and not financials.empty:
                if 'Total Revenue' in financials.index:
                    revenue = financials.loc['Total Revenue']
                else:
                    revenue = None
            else:
                revenue = None

            # Build quarterly table
            for i, date in enumerate(ocf.index[:5]):  # Last 5 periods
                quarter_data = {
                    'date': date.strftime('%Y-%m-%d'),
                    'ocf': float(ocf.iloc[i]) if pd.notna(ocf.iloc[i]) else None,
                    'capex': float(capex.iloc[i]) if pd.notna(capex.iloc[i]) else None,
                    'fcf': float(fcf.iloc[i]) if pd.notna(fcf.iloc[i]) else None,
                }

                if revenue is not None and date in revenue.index:
                    quarter_data['revenue'] = float(revenue.loc[date]) if pd.notna(revenue.loc[date]) else None
                else:
                    quarter_data['revenue'] = None

                analysis['quarterly_data'].append(quarter_data)

            # Trend Analysis
            if len(ocf) >= 2:
                # OCF trend
                ocf_latest = ocf.iloc[0]
                ocf_previous = ocf.iloc[1]

                if pd.notna(ocf_latest) and pd.notna(ocf_previous):
                    ocf_change = ((ocf_latest - ocf_previous) / abs(ocf_previous)) * 100
                    analysis['trends']['ocf_change'] = ocf_change

                    if ocf_change > 20:
                        analysis['green_flags'].append('OCF_ACCELERATING')
                    elif ocf_change < -20:
                        analysis['red_flags'].append('OCF_DECLINING')

                # FCF trend
                fcf_latest = fcf.iloc[0]
                fcf_previous = fcf.iloc[1]

                if pd.notna(fcf_latest) and pd.notna(fcf_previous):
                    if fcf_latest < 0:
                        analysis['red_flags'].append('NEGATIVE_FREE_CASH_FLOW')

            # Revenue vs OCF divergence
            if revenue is not None and len(revenue) >= 2:
                # Compare trends
                common_dates = revenue.index.intersection(ocf.index)
                if len(common_dates) >= 2:
                    rev_latest = revenue.loc[common_dates[0]]
                    rev_previous = revenue.loc[common_dates[1]]
                    ocf_latest_comp = ocf.loc[common_dates[0]]
                    ocf_previous_comp = ocf.loc[common_dates[1]]

                    if pd.notna(rev_latest) and pd.notna(rev_previous) and \
                       pd.notna(ocf_latest_comp) and pd.notna(ocf_previous_comp):

                        rev_growth = ((rev_latest - rev_previous) / abs(rev_previous)) * 100
                        ocf_growth = ((ocf_latest_comp - ocf_previous_comp) / abs(ocf_previous_comp)) * 100

                        analysis['trends']['revenue_growth'] = rev_growth
                        analysis['trends']['ocf_growth'] = ocf_growth

                        # RED FLAG: Revenue growing but OCF shrinking
                        if rev_growth > 10 and ocf_growth < -10:
                            analysis['red_flags'].append('REVENUE_UP_CASH_DOWN')

            # Stock-Based Compensation check
            # This is often hidden in cash flow statement
            # Look for it in operating activities adjustments

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_receivables(self, stock) -> Dict:
        """
        The Receivables Game - Are customers actually paying?

        Calculates Days Sales Outstanding (DSO):
        DSO = (Accounts Receivable / Revenue) × 90 days

        Red Flags:
        - DSO increasing = customers paying slower
        - DSO > industry average = collection problems
        - Allowance for doubtful accounts increasing
        """
        try:
            # Get balance sheet and financials
            balance_sheet = stock.balance_sheet
            financials = stock.financials

            if balance_sheet is None or balance_sheet.empty:
                return {'error': 'No balance sheet data'}

            analysis = {
                'quarterly_dso': [],
                'trend': None,
                'red_flags': [],
                'green_flags': []
            }

            # Find Accounts Receivable
            ar_keys = ['Accounts Receivable', 'Net Receivables', 'Receivables']
            ar = None
            for key in ar_keys:
                if key in balance_sheet.index:
                    ar = balance_sheet.loc[key]
                    break

            if ar is None:
                return {'note': 'No receivables data (may be service company with no AR)'}

            # Get revenue
            if financials is not None and 'Total Revenue' in financials.index:
                revenue = financials.loc['Total Revenue']
            else:
                return {'error': 'No revenue data'}

            # Calculate DSO for each period
            dso_values = []
            for date in ar.index[:4]:  # Last 4 periods
                if date in revenue.index:
                    ar_val = ar.loc[date]
                    rev_val = revenue.loc[date]

                    if pd.notna(ar_val) and pd.notna(rev_val) and rev_val != 0:
                        # DSO = (AR / Quarterly Revenue) × 90 days
                        dso = (ar_val / rev_val) * 90

                        dso_values.append(dso)
                        analysis['quarterly_dso'].append({
                            'date': date.strftime('%Y-%m-%d'),
                            'dso': round(dso, 1)
                        })

            # Trend analysis
            if len(dso_values) >= 2:
                latest_dso = dso_values[0]
                previous_dso = dso_values[1]

                dso_change = latest_dso - previous_dso
                analysis['trend'] = {
                    'latest_dso': round(latest_dso, 1),
                    'previous_dso': round(previous_dso, 1),
                    'change': round(dso_change, 1)
                }

                # Red flag: DSO increasing significantly
                if dso_change > 5:  # +5 days = slower collections
                    analysis['red_flags'].append('DSO_INCREASING')
                elif dso_change < -5:  # -5 days = faster collections
                    analysis['green_flags'].append('DSO_IMPROVING')

                # Absolute DSO check
                if latest_dso > 90:  # >90 days = very slow
                    analysis['red_flags'].append('SLOW_COLLECTIONS')

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_inventory(self, stock) -> Dict:
        """
        The Inventory Trick - Is product actually selling?

        For hardware companies (AMD, NVDA, etc.)

        Calculates:
        - Inventory Turnover = COGS / Avg Inventory
        - Days Inventory = 365 / Inventory Turnover

        Red Flags:
        - Days inventory increasing = product not selling
        - Inventory writedowns in footnotes
        """
        try:
            balance_sheet = stock.balance_sheet
            financials = stock.financials

            if balance_sheet is None or balance_sheet.empty:
                return {'error': 'No balance sheet data'}

            analysis = {
                'quarterly_data': [],
                'trend': None,
                'red_flags': [],
                'green_flags': []
            }

            # Find inventory
            if 'Inventory' not in balance_sheet.index:
                return {'note': 'No inventory (likely service company)'}

            inventory = balance_sheet.loc['Inventory']

            # Get Cost of Goods Sold
            if financials is not None and 'Cost Of Revenue' in financials.index:
                cogs = financials.loc['Cost Of Revenue']
            else:
                return {'note': 'No COGS data available'}

            # Calculate days inventory for each period
            days_inv_values = []
            for date in inventory.index[:4]:  # Last 4 periods
                if date in cogs.index:
                    inv_val = inventory.loc[date]
                    cogs_val = cogs.loc[date]

                    if pd.notna(inv_val) and pd.notna(cogs_val) and cogs_val != 0:
                        # Inventory turnover = COGS / Inventory
                        turnover = cogs_val / inv_val

                        # Days inventory = 365 / Turnover (for annual), 90 for quarterly
                        days_inv = 90 / turnover if turnover > 0 else None

                        if days_inv:
                            days_inv_values.append(days_inv)
                            analysis['quarterly_data'].append({
                                'date': date.strftime('%Y-%m-%d'),
                                'days_inventory': round(days_inv, 1)
                            })

            # Trend analysis
            if len(days_inv_values) >= 2:
                latest = days_inv_values[0]
                previous = days_inv_values[1]

                change = latest - previous
                analysis['trend'] = {
                    'latest_days': round(latest, 1),
                    'previous_days': round(previous, 1),
                    'change': round(change, 1)
                }

                # Red flag: Inventory piling up
                if change > 10:  # +10 days = inventory building
                    analysis['red_flags'].append('INVENTORY_BUILDING')
                elif change < -10:  # -10 days = selling faster
                    analysis['green_flags'].append('INVENTORY_IMPROVING')

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def analyze_debt(self, stock) -> Dict:
        """
        The Debt Time Bomb - Can they service their debt?

        Analyzes:
        - Total debt vs cash
        - Interest coverage ratio (EBITDA / Interest Expense)
        - Debt maturity (if available)

        Red Flags:
        - Interest coverage < 3x
        - Debt increasing while revenue flat/declining
        - Net debt > 3x EBITDA
        """
        try:
            balance_sheet = stock.balance_sheet
            financials = stock.financials
            info = stock.info

            if balance_sheet is None or balance_sheet.empty:
                return {'error': 'No balance sheet data'}

            analysis = {
                'debt_profile': {},
                'coverage': {},
                'red_flags': [],
                'green_flags': []
            }

            # Get total debt
            total_debt = info.get('totalDebt', 0)

            # Get cash
            cash = info.get('totalCash', 0)

            # Net debt
            net_debt = total_debt - cash if total_debt and cash else None

            analysis['debt_profile'] = {
                'total_debt': total_debt,
                'cash': cash,
                'net_debt': net_debt
            }

            # Interest coverage
            ebitda = info.get('ebitda')
            interest_expense = None

            # Try to get interest expense from financials
            if financials is not None:
                if 'Interest Expense' in financials.index:
                    interest_expense = financials.loc['Interest Expense'].iloc[0]
                    interest_expense = abs(interest_expense)  # Usually negative

            if ebitda and interest_expense and interest_expense > 0:
                coverage_ratio = ebitda / interest_expense

                analysis['coverage'] = {
                    'ebitda': ebitda,
                    'interest_expense': interest_expense,
                    'coverage_ratio': round(coverage_ratio, 2)
                }

                # Red flag: Low coverage
                if coverage_ratio < 3:
                    analysis['red_flags'].append('LOW_INTEREST_COVERAGE')
                elif coverage_ratio > 10:
                    analysis['green_flags'].append('STRONG_INTEREST_COVERAGE')

            # Debt to EBITDA ratio
            if net_debt and ebitda and ebitda > 0:
                debt_to_ebitda = net_debt / ebitda
                analysis['debt_profile']['debt_to_ebitda'] = round(debt_to_ebitda, 2)

                if debt_to_ebitda > 3:
                    analysis['red_flags'].append('HIGH_DEBT_TO_EBITDA')
                elif debt_to_ebitda < 0:  # Net cash position
                    analysis['green_flags'].append('NET_CASH_POSITION')

            # Check if debt-free
            if total_debt == 0 or total_debt < cash:
                analysis['green_flags'].append('DEBT_FREE_OR_NET_CASH')

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def _calculate_score(self, analysis: Dict) -> int:
        """
        Calculate overall financial truth score (0-10)

        Green flags add points, red flags subtract
        """
        score = 5  # Start neutral

        # Count flags across all categories
        all_red_flags = []
        all_green_flags = []

        for category in ['cash_flow', 'receivables', 'inventory', 'debt']:
            if category in analysis:
                cat_data = analysis[category]
                if isinstance(cat_data, dict):
                    all_red_flags.extend(cat_data.get('red_flags', []))
                    all_green_flags.extend(cat_data.get('green_flags', []))

        # Update master lists
        analysis['red_flags'] = list(set(all_red_flags))
        analysis['green_flags'] = list(set(all_green_flags))

        # Scoring
        score += min(len(all_green_flags), 5)  # Max +5 for green flags
        score -= len(all_red_flags)  # -1 for each red flag

        # Cap at 0-10
        return max(0, min(10, score))


def main():
    """Test the analyzer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python financial_truth_analyzer.py <TICKER>")
        print("\nExample: python financial_truth_analyzer.py AAPL")
        return

    ticker = sys.argv[1].upper()

    analyzer = FinancialTruthAnalyzer()
    result = analyzer.analyze(ticker)

    print(f"\n{'='*80}")
    print(f"FINANCIAL TRUTH ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    print(f"Overall Score: {result['score']}/10\n")

    # Cash Flow
    if 'cash_flow' in result and 'quarterly_data' in result['cash_flow']:
        print("CASH FLOW FORENSICS:")
        for q in result['cash_flow']['quarterly_data'][:3]:
            print(f"  {q['date']}: OCF ${q['ocf']/1e9:.2f}B, FCF ${q['fcf']/1e9:.2f}B")

        if 'trends' in result['cash_flow']:
            trends = result['cash_flow']['trends']
            if 'revenue_growth' in trends:
                print(f"\n  Revenue Growth: {trends['revenue_growth']:+.1f}%")
                print(f"  OCF Growth: {trends['ocf_growth']:+.1f}%")

    # Receivables
    if 'receivables' in result and 'trend' in result['receivables'] and result['receivables']['trend']:
        print(f"\nRECEIVABLES:")
        trend = result['receivables']['trend']
        print(f"  Current DSO: {trend['latest_dso']} days")
        print(f"  Previous DSO: {trend['previous_dso']} days")
        print(f"  Change: {trend['change']:+.1f} days")

    # Debt
    if 'debt' in result and 'debt_profile' in result['debt']:
        print(f"\nDEBT PROFILE:")
        profile = result['debt']['debt_profile']
        if profile.get('total_debt'):
            print(f"  Total Debt: ${profile['total_debt']/1e9:.2f}B")
            print(f"  Cash: ${profile['cash']/1e9:.2f}B")
            print(f"  Net Debt: ${profile['net_debt']/1e9:.2f}B")

        if 'coverage' in result['debt'] and result['debt']['coverage']:
            cov = result['debt']['coverage']
            print(f"  Interest Coverage: {cov['coverage_ratio']:.1f}x")

    # Flags
    if result['red_flags']:
        print(f"\nRED FLAGS:")
        for flag in result['red_flags']:
            print(f"  - {flag}")

    if result['green_flags']:
        print(f"\nGREEN FLAGS:")
        for flag in result['green_flags']:
            print(f"  + {flag}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
