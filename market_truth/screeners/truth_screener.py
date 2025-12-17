"""
Market Truth Screener - Batch Analysis with Professional Screener
Combines technical signals from professional_screener with deep fundamental analysis
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from src.professional_screener import ProfessionalStockScreener
from src.market_truth_framework import MarketTruthFramework


class MarketTruthScreener:
    """
    Complete screening system combining:
    - Professional screener (technical + basic fundamentals)
    - Market Truth Framework (deep multi-layer analysis)
    """

    def __init__(self, min_market_cap=10e9):
        self.min_market_cap = min_market_cap
        self.professional_screener = ProfessionalStockScreener(min_market_cap)
        self.truth_framework = MarketTruthFramework()

    def screen_with_truth_analysis(self, max_stocks=10, min_combined_score=40):
        """
        Run professional screener first, then deep-dive with Market Truth Framework

        Args:
            max_stocks: Number of top stocks to analyze with MTF (default 10)
            min_combined_score: Minimum combined score to be considered (default 40)

        Returns:
            DataFrame with combined analysis
        """
        print("="*80)
        print("MARKET TRUTH SCREENER")
        print("="*80)
        print()

        # Step 1: Professional screener for initial filtering
        print("[STAGE 1] Running Professional Screener on S&P 500...")
        print()

        screener_results, regime, strategy = self.professional_screener.screen()

        if len(screener_results) == 0:
            print("\n[X] No opportunities found by professional screener")
            return pd.DataFrame(), regime, strategy

        print(f"\n[OK] Found {len(screener_results)} opportunities")
        print(f"    Taking top {max_stocks} for deep Market Truth analysis...")
        print()

        # Step 2: Deep analysis on top candidates
        print("[STAGE 2] Running Market Truth Framework on Top Candidates...")
        print("="*80)
        print()

        top_candidates = screener_results.head(max_stocks)
        enhanced_results = []

        for idx, row in top_candidates.iterrows():
            ticker = row['ticker']

            print(f"\n{'='*80}")
            print(f"Analyzing {ticker} ({idx+1}/{len(top_candidates)})")
            print(f"{'='*80}")

            try:
                # Run Market Truth Framework
                mtf_analysis = self.truth_framework.analyze(ticker)

                # Map technical score to 0-10 scale for MTF integration
                # Professional screener max is ~30, normalize to 10
                technical_score_normalized = min(10, int((row['score'] / 30) * 10))

                # Update MTF analysis with technical score
                mtf_analysis['layers']['technical'] = {
                    'score': technical_score_normalized,
                    'raw_score': row['score'],
                    'setup': row['setup_types'],
                    'confidence': row['confidence']
                }

                # Recalculate MTF total with technical included
                mtf_total_with_technical = (
                    technical_score_normalized +
                    mtf_analysis['layers'].get('business_model', {}).get('score', 0) +
                    mtf_analysis['layers'].get('financial_truth', {}).get('score', 0) +
                    mtf_analysis['layers'].get('management', {}).get('score', 0) +
                    mtf_analysis['layers'].get('market_structure', {}).get('score', 0) +
                    mtf_analysis['layers'].get('competitive', {}).get('score', 0) +
                    mtf_analysis['layers'].get('macro', {}).get('score', 0)
                )

                # Re-evaluate disqualifiers with technical score
                disqualifiers = []
                for layer_name, layer_data in mtf_analysis['layers'].items():
                    if isinstance(layer_data, dict) and layer_data.get('score', 10) < 3:
                        disqualifiers.append(f"{layer_name.upper()}_DISQUALIFIER")

                is_disqualified = len(disqualifiers) > 0

                # Re-determine action with updated score
                if mtf_total_with_technical >= 60:
                    mtf_action = 'HIGH_CONVICTION_LONG'
                    mtf_timeframe = '6+ months'
                elif mtf_total_with_technical >= 50:
                    mtf_action = 'POSITION_TRADE'
                    mtf_timeframe = '3-6 months'
                elif mtf_total_with_technical >= 40:
                    mtf_action = 'SWING_TRADE'
                    mtf_timeframe = 'Weeks'
                elif mtf_total_with_technical >= 30:
                    mtf_action = 'SPECULATION'
                    mtf_timeframe = 'Days'
                else:
                    mtf_action = 'AVOID'
                    mtf_timeframe = 'Do not trade'

                # Combine results
                combined = {
                    # From professional screener
                    'ticker': ticker,
                    'technical_score': row['score'],
                    'technical_score_normalized': technical_score_normalized,
                    'setup_types': row['setup_types'],
                    'confidence': row['confidence'],
                    'current_price': row['current_price'],
                    'sector': row['sector'],
                    'industry': row['industry'],

                    # Trading recommendations
                    'direction': row.get('direction', 'N/A'),
                    'entry_timing': row.get('entry_timing', 'N/A'),
                    'stop_loss': row.get('stop_loss', 0),
                    'take_profit_1': row.get('take_profit_1', 0),
                    'risk_reward': row.get('risk_reward_ratio', 0),
                    'hold_duration': row.get('hold_duration', {}).get('duration', 'N/A'),

                    # From Market Truth Framework
                    'business_model_score': mtf_analysis['layers'].get('business_model', {}).get('score', 0),
                    'financial_truth_score': mtf_analysis['layers'].get('financial_truth', {}).get('score', 0),
                    'management_score': mtf_analysis['layers'].get('management', {}).get('score', 0),
                    'market_structure_score': mtf_analysis['layers'].get('market_structure', {}).get('score', 0),
                    'competitive_score': mtf_analysis['layers'].get('competitive', {}).get('score', 0),
                    'macro_score': mtf_analysis['layers'].get('macro', {}).get('score', 0),

                    # Synthesis (updated)
                    'mtf_total_score': mtf_total_with_technical,
                    'mtf_action': mtf_action,
                    'mtf_timeframe': mtf_timeframe,
                    'disqualified': is_disqualified,
                    'disqualifiers': ','.join(disqualifiers),

                    # Combined score (technical + fundamental weighted)
                    'combined_score': self._calculate_combined_score_v2(
                        row['score'],
                        mtf_total_with_technical,
                        is_disqualified
                    ),
                }

                enhanced_results.append(combined)

                # Show summary
                print(f"\n   Technical Score: {row['score']}")
                print(f"   MTF Total Score: {mtf_analysis['synthesis']['total_score']}/70")
                print(f"   Combined Score: {combined['combined_score']:.1f}")
                print(f"   MTF Action: {mtf_analysis['synthesis']['action']}")

                if mtf_analysis['synthesis']['disqualified']:
                    print(f"   ⚠️  DISQUALIFIED: {combined['disqualifiers']}")

            except Exception as e:
                print(f"   [ERROR] Failed to analyze {ticker}: {e}")
                continue

        if not enhanced_results:
            print("\n[X] No stocks passed Market Truth analysis")
            return pd.DataFrame(), regime, strategy

        # Create final DataFrame
        df = pd.DataFrame(enhanced_results)

        # Sort by combined score
        df = df.sort_values('combined_score', ascending=False)

        # Filter by minimum combined score
        df_filtered = df[df['combined_score'] >= min_combined_score].copy()

        print(f"\n[FILTER] {len(df_filtered)}/{len(df)} stocks passed minimum score threshold ({min_combined_score})")

        return df_filtered, regime, strategy

    def _calculate_combined_score(self, technical_score, mtf_analysis):
        """
        Calculate weighted combined score

        Technical score (max ~25): 40% weight
        MTF score (max 70): 60% weight

        Normalized to 100
        """
        # Normalize technical score (assume max 25)
        tech_normalized = (technical_score / 25) * 40

        # Normalize MTF score
        mtf_normalized = (mtf_analysis['synthesis']['total_score'] / 70) * 60

        combined = tech_normalized + mtf_normalized

        # Penalty if disqualified
        if mtf_analysis['synthesis']['disqualified']:
            combined *= 0.5

        return combined

    def _calculate_combined_score_v2(self, technical_score, mtf_total, is_disqualified):
        """
        Improved combined score calculation

        Technical score (max 30): 30% weight
        MTF total (max 70): 70% weight

        Normalized to 100
        """
        # Normalize scores
        tech_normalized = (technical_score / 30) * 30
        mtf_normalized = (mtf_total / 70) * 70

        combined = tech_normalized + mtf_normalized

        # Smaller penalty for minor disqualifiers (technical only)
        # Bigger penalty for fundamental disqualifiers
        if is_disqualified:
            combined *= 0.7  # 30% penalty instead of 50%

        return combined

    def display_results(self, df, regime, strategy):
        """Display comprehensive results"""

        if len(df) == 0:
            print("\n[X] No opportunities found")
            return

        print("\n" + "="*80)
        print(f"FINAL RESULTS - {len(df)} HIGH-QUALITY OPPORTUNITIES")
        print("="*80)
        print()
        print(f"Market Regime: {regime['regime']} ({regime['confidence']}% confidence)")
        print(f"Strategy: {strategy['strategy']}")
        print()

        # Show top 5
        top_5 = df.head(5)

        for i, row in top_5.iterrows():
            print("="*80)
            print(f"#{i+1}. {row['ticker']} - {row['sector']}")
            print("="*80)
            print(f"   Combined Score: {row['combined_score']:.1f}/100")
            print()
            print(f"   TECHNICAL ANALYSIS:")
            print(f"      Raw Score: {row['technical_score']}")
            print(f"      Normalized: {row['technical_score_normalized']}/10")
            print(f"      Setup: {row['setup_types']}")
            print(f"      Confidence: {row['confidence']}")
            print(f"      Direction: {row['direction']}")
            print(f"      Entry: {row['entry_timing']}")
            print()
            print(f"   FUNDAMENTAL LAYERS:")
            print(f"      Technical:         {row['technical_score_normalized']}/10")
            print(f"      Business Model:    {row['business_model_score']}/10")
            print(f"      Financial Truth:   {row['financial_truth_score']}/10")
            print(f"      Management:        {row['management_score']}/10")
            print(f"      Market Structure:  {row['market_structure_score']}/10")
            print(f"      Competitive:       {row['competitive_score']}/10")
            print(f"      Macro Forces:      {row['macro_score']}/10")
            print(f"      MTF Total:         {row['mtf_total_score']}/70")
            print()
            print(f"   RECOMMENDATION:")
            print(f"      MTF Action: {row['mtf_action']}")
            print(f"      Timeframe: {row['mtf_timeframe']}")
            print(f"      Hold Duration: {row['hold_duration']}")
            print()

            if row['direction'] != 'NEUTRAL' and row['stop_loss'] > 0:
                print(f"   RISK MANAGEMENT:")
                print(f"      Price: ${row['current_price']:.2f}")
                print(f"      Stop Loss: ${row['stop_loss']:.2f}")
                print(f"      Target: ${row['take_profit_1']:.2f}")
                print(f"      Risk/Reward: {row['risk_reward']:.1f}:1")
                print()

            if row['disqualified']:
                print(f"   ⚠️  WARNINGS: {row['disqualifiers']}")
                print()

        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"market_truth_screener_{timestamp}.csv"
        df.to_csv(filename, index=False)
        print(f"\n[SAVE] Full results saved to: {filename}")
        print("="*80)


def main():
    """Run Market Truth Screener"""
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    screener = MarketTruthScreener(min_market_cap=10e9)

    # Run screening (analyze top 15 from professional screener, min score 50)
    results, regime, strategy = screener.screen_with_truth_analysis(
        max_stocks=15,
        min_combined_score=50  # Only show high-quality opportunities
    )

    # Display results
    screener.display_results(results, regime, strategy)


if __name__ == "__main__":
    main()
