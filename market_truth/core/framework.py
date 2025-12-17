"""
Market Truth Framework - Multi-Layer Intelligence System
A systematic approach to finding structural truth in markets

Architecture:
    Layer 1: Technical Signal (professional_screener.py) - Already built
    Layer 2: Business Model Forensics - Revenue quality, unit economics, moat
    Layer 3: Financial Truth Extraction - Cash flow, receivables, debt
    Layer 4: Management Truth Detection - Insider activity, communication, compensation
    Layer 5: Market Structure & Incentives - Float, short interest, options
    Layer 6: Competitive Dynamics - TAM reality, competitive landscape
    Layer 7: Macro Forces - Interest rates, liquidity, narrative cycle
    Layer 8: Synthesis - Cross-layer reasoning and industry-weighted scoring
    Layer 9: Execution - Position sizing and monitoring

Philosophy: Revenue is opinion, cash is fact. Find structural truth before the market.

Version 2.0: Now with cross-layer intelligence, industry weighting, and temporal tracking
"""
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# Import layer analyzers
from market_truth.analyzers.financial_truth import FinancialTruthAnalyzer
from market_truth.analyzers.business_model import BusinessModelAnalyzer
from market_truth.analyzers.management_truth import ManagementTruthDetector
from market_truth.analyzers.market_structure import MarketStructureAnalyzer
from market_truth.analyzers.competitive_dynamics import CompetitiveDynamicsAnalyzer
from market_truth.analyzers.macro_forces import MacroForcesAnalyzer
from market_truth.analyzers.risk_assessment import RiskAssessmentAnalyzer

# Import intelligence core
from market_truth.core.layer_schema import LayerOutput
from market_truth.core.synthesis_engine import SynthesisEngine
from market_truth.core.temporal_engine import TemporalEngine
from market_truth.core.api_manager import get_api_manager


class MarketTruthFramework:
    """
    Complete multi-layer due diligence system with intelligence core

    Version 2.0: Now features:
    - Cross-layer reasoning (layers inform each other)
    - Industry-specific weighting (software != banks)
    - Temporal tracking (momentum matters)
    - Bayesian belief updates (not just score summing)

    Usage:
        mtf = MarketTruthFramework()
        analysis = mtf.analyze('AAPL')
        print(f"Conviction: {analysis['synthesis']['conviction']}")
    """

    def __init__(self):
        # Initialize API manager (handles FMP, SEC, yfinance with rate limiting)
        self.api_manager = get_api_manager()

        # Check API status
        api_status = self.api_manager.get_api_status()
        print("\n[API Status]")
        for api, available in api_status.items():
            icon = "+" if available else "x"
            print(f"  [{icon}] {api}: {available}")

        # Initialize layer analyzers with API manager
        self.business_model_analyzer = BusinessModelAnalyzer(api_manager=self.api_manager)
        self.financial_analyzer = FinancialTruthAnalyzer(api_manager=self.api_manager)
        self.management_detector = ManagementTruthDetector(api_manager=self.api_manager)
        self.market_structure_analyzer = MarketStructureAnalyzer(api_manager=self.api_manager)
        self.competitive_analyzer = CompetitiveDynamicsAnalyzer(api_manager=self.api_manager)
        self.macro_analyzer = MacroForcesAnalyzer(api_manager=self.api_manager)
        self.risk_analyzer = RiskAssessmentAnalyzer(api_manager=self.api_manager)

        # Initialize intelligence core
        self.synthesis_engine = SynthesisEngine()
        self.temporal_engine = TemporalEngine()

    def analyze(self, ticker: str) -> Dict:
        """
        Run complete Market Truth Framework analysis on a ticker

        Returns comprehensive analysis with scores for all 7 layers
        """
        print(f"\n{'='*80}")
        print(f"MARKET TRUTH FRAMEWORK ANALYSIS: {ticker}")
        print(f"{'='*80}\n")

        analysis = {
            'ticker': ticker,
            'timestamp': datetime.now(),
            'layers': {}
        }

        # Layer 1: Technical Signal (from professional_screener.py)
        # This is your entry point - already built
        analysis['layers']['technical'] = {
            'score': 0,
            'note': 'Run professional_screener.py first to get technical score'
        }

        # Layer 2: Business Model Forensics
        print("Analyzing business model...")
        try:
            time.sleep(0.5)  # Small delay between layers
            analysis['layers']['business_model'] = self.business_model_analyzer.analyze(ticker)
        except Exception as e:
            print(f"Business model analysis failed: {e}")
            analysis['layers']['business_model'] = {'score': 0, 'error': str(e)}

        # Layer 3: Financial Truth
        print("Extracting financial truth...")
        try:
            time.sleep(0.5)
            analysis['layers']['financial_truth'] = self.analyze_financial_truth(ticker)
        except Exception as e:
            print(f"Financial analysis failed: {e}")
            analysis['layers']['financial_truth'] = {'score': 0, 'error': str(e)}

        # Layer 4: Management Quality
        print("Detecting management truth...")
        try:
            time.sleep(0.5)
            analysis['layers']['management'] = self.management_detector.analyze(ticker)
        except Exception as e:
            print(f"Management analysis failed: {e}")
            analysis['layers']['management'] = {'score': 0, 'error': str(e)}

        # Layer 5: Market Structure
        print("Analyzing market structure...")
        try:
            time.sleep(0.5)
            analysis['layers']['market_structure'] = self.market_structure_analyzer.analyze(ticker)
        except Exception as e:
            print(f"Market structure analysis failed: {e}")
            analysis['layers']['market_structure'] = {'score': 0, 'error': str(e)}

        # Layer 6: Competitive Position
        print("Mapping competitive landscape...")
        try:
            time.sleep(0.5)
            analysis['layers']['competitive'] = self.competitive_analyzer.analyze(ticker)
        except Exception as e:
            print(f"Competitive analysis failed: {e}")
            analysis['layers']['competitive'] = {'score': 0, 'error': str(e)}

        # Layer 7: Macro Alignment
        print("Checking macro forces...")
        try:
            time.sleep(0.5)
            analysis['layers']['macro'] = self.macro_analyzer.analyze(ticker)
        except Exception as e:
            print(f"Macro analysis failed: {e}")
            analysis['layers']['macro'] = {'score': 0, 'error': str(e)}

        # Layer 8: Risk Assessment
        print("Assessing overall risk...")
        try:
            time.sleep(0.5)
            analysis['layers']['risk'] = self.risk_analyzer.analyze(ticker)
        except Exception as e:
            print(f"Risk assessment failed: {e}")
            analysis['layers']['risk'] = {'score': 5, 'error': str(e)}

        # Get company info for industry weighting
        try:
            stock_data = self.api_manager.get_stock_data(ticker)
            if stock_data['source'] == 'FMP' and stock_data['data']:
                # FMP profile data
                profile = stock_data['data']
                sector = profile.get('sector')
                industry = profile.get('industry')
            else:
                # yfinance data
                stock = stock_data['data']
                info = stock.info
                sector = info.get('sector')
                industry = info.get('industry')
        except Exception as e:
            print(f"[Warning] Could not get sector/industry: {e}")
            sector = None
            industry = None

        # Normalize all layers to standard format
        normalized_layers = {}
        for layer_name, layer_data in analysis['layers'].items():
            if isinstance(layer_data, dict) and 'error' not in layer_data:
                normalized_layers[layer_name] = LayerOutput.normalize(layer_data)
            elif isinstance(layer_data, dict) and 'error' in layer_data:
                normalized_layers[layer_name] = LayerOutput.create_empty(layer_data.get('error', 'Unknown error'))
            else:
                normalized_layers[layer_name] = LayerOutput.create_empty("Invalid layer output")

        # Update analysis with normalized layers
        analysis['layers_normalized'] = normalized_layers

        # Layer 9: Synthesis (Intelligence Core)
        print("\nRunning synthesis engine...")
        synthesis = self.synthesis_engine.synthesize(
            layers=normalized_layers,
            ticker=ticker,
            sector=sector,
            industry=industry
        )
        analysis['synthesis'] = synthesis

        # Temporal tracking
        try:
            self.temporal_engine.save_analysis(ticker, analysis, synthesis)
            temporal = self.temporal_engine.get_temporal_analysis(ticker)
            if temporal:
                analysis['temporal'] = temporal
        except Exception as e:
            print(f"[Warning] Temporal tracking failed: {e}")
            analysis['temporal'] = None

        return analysis


    def analyze_financial_truth(self, ticker: str) -> Dict:
        """
        Layer 3: Financial Truth Extraction

        The Golden Rule: Revenue is opinion, cash is fact

        Analyzes:
        - Cash flow vs earnings (is profit real?)
        - Receivables trend (are customers paying?)
        - Inventory trend (is product selling?)
        - Debt profile (time bomb?)

        Returns score 0-10
        """
        return self.financial_analyzer.analyze(ticker)


    def synthesize_analysis(self, analysis: Dict) -> Dict:
        """
        DEPRECATED: Legacy synthesis method (kept for backward compatibility)

        Use analysis['synthesis'] instead, which uses the new SynthesisEngine
        with cross-layer reasoning and industry weighting
        """
        # Return simplified legacy format if called
        if 'synthesis' in analysis:
            synth = analysis['synthesis']
            return {
                'total_score': synth.get('raw_score', 0),
                'weighted_score': synth.get('weighted_score', 0),
                'action': synth.get('action', 'UNKNOWN'),
                'conviction': synth.get('conviction', 'UNKNOWN'),
                'disqualified': synth.get('disqualified', False),
                'note': 'Using new synthesis engine - see analysis["synthesis"] for full details'
            }

        # Fallback if synthesis not run yet
        layers = analysis['layers']
        total_score = sum([
            layers.get('business_model', {}).get('score', 0),
            layers.get('financial_truth', {}).get('score', 0),
            layers.get('management', {}).get('score', 0),
            layers.get('market_structure', {}).get('score', 0),
            layers.get('competitive', {}).get('score', 0),
            layers.get('macro', {}).get('score', 0),
            layers.get('risk', {}).get('score', 0)
        ])

        return {
            'total_score': total_score,
            'max_score': 70,
            'action': 'RUN_NEW_SYNTHESIS',
            'note': 'Legacy method - run analyze() for full intelligence'
        }


def main():
    """Test the framework"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python market_truth_framework.py <TICKER>")
        print("\nExample: python market_truth_framework.py AAPL")
        return

    ticker = sys.argv[1].upper()

    mtf = MarketTruthFramework()
    analysis = mtf.analyze(ticker)

    # Display results
    print(f"\n{'='*80}")
    print(f"MARKET TRUTH ANALYSIS RESULTS: {ticker}")
    print(f"{'='*80}\n")

    # Layer scores
    print("LAYER SCORES (Raw):")
    for layer_name, layer_data in analysis['layers'].items():
        if isinstance(layer_data, dict):
            score = layer_data.get('score', 'N/A')
            trajectory = analysis.get('layers_normalized', {}).get(layer_name, {}).get('trajectory', '')
            trajectory_icon = {'improving': '^', 'deteriorating': 'v', 'stable': '->'}.get(trajectory, '')
            print(f"  {layer_name.replace('_', ' ').title():30s} {score}/10 {trajectory_icon} {trajectory}")

    # Synthesis results
    synthesis = analysis['synthesis']
    print(f"\n{'='*80}")
    print(f"SYNTHESIS (Intelligence Core)")
    print(f"{'='*80}")
    print(f"Raw Score:      {synthesis.get('raw_score', 0):.1f}/70")
    print(f"Weighted Score: {synthesis.get('weighted_score', 0):.1f}/100")
    print(f"\nConviction:     {synthesis.get('conviction', 'UNKNOWN')}")
    print(f"Action:         {synthesis.get('action', 'UNKNOWN')}")
    print(f"Reasoning:      {synthesis.get('reasoning', 'N/A')}")

    # Belief state
    if 'belief_state' in synthesis:
        belief = synthesis['belief_state']
        print(f"\nBELIEF STATE (Bayesian Probabilities):")
        print(f"  P(Structural Bull): {belief.get('bull_prob', 0):.1%}")
        print(f"  P(Structural Bear): {belief.get('bear_prob', 0):.1%}")
        print(f"  P(Distress Risk):   {belief.get('distress_prob', 0):.1%}")

    # Overrides
    if synthesis.get('disqualified'):
        print(f"\n⚠️  STRUCTURAL DISQUALIFIERS:")
        for override in synthesis.get('override_rules', []):
            print(f"  - {override}")

    # Temporal changes (if available)
    if analysis.get('temporal') and 'summary' in analysis['temporal']:
        temporal = analysis['temporal']
        print(f"\n{'='*80}")
        print(f"TEMPORAL ANALYSIS (Changes Since Last Run)")
        print(f"{'='*80}")
        print(f"{temporal['summary'].get('headline', 'No headline')}")

        if temporal['summary'].get('key_changes'):
            print(f"\nKey Changes:")
            for change in temporal['summary']['key_changes']:
                print(f"  - {change}")

        print(f"\nRecommendation: {temporal['summary'].get('recommendation', 'N/A')}")

    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
