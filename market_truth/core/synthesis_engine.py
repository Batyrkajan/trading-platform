"""
Synthesis Engine - The Intelligence Core
Where layers talk to each other and form structural beliefs

This is not a score adder. This is a reasoning engine.

Key Capabilities:
1. Cross-Layer Inference (debt + insider selling = override to avoid)
2. Industry-Weighted Scoring (software moat matters 4x more than debt)
3. Bayesian Belief Updates (layers inform each other, not just sum)
4. Structural Override Rules (some combinations disqualify immediately)
"""
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from typing import Dict, List, Optional, Tuple
import numpy as np
from pathlib import Path

from market_truth.core.layer_schema import LayerOutput


class SynthesisEngine:
    """
    The brain of the Market Truth Framework

    Takes normalized layer outputs and:
    - Applies industry-specific weights
    - Runs cross-layer inference rules
    - Updates beliefs based on layer interactions
    - Issues structural overrides when needed
    """

    def __init__(self):
        # Load industry weights (from project root config/)
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "industry_weights.json"
        with open(config_path, 'r') as f:
            self.industry_weights = json.load(f)

        self.default_weights = self.industry_weights.get('_default_weights', {})

    def synthesize(
        self,
        layers: Dict[str, Dict],
        ticker: str,
        sector: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Dict:
        """
        Main synthesis function

        Args:
            layers: Dict of normalized layer outputs from LayerOutput.normalize()
            ticker: Stock ticker
            sector: Company sector (for industry weights)
            industry: Company industry

        Returns:
            Comprehensive synthesis with:
            - weighted_score: Industry-adjusted total score
            - conviction: high/medium/low/avoid/short
            - structural_overrides: List of disqualifying combinations
            - belief_state: Bayesian probability estimates
            - reasoning: Explanation of decision
        """
        print(f"\n{'='*80}")
        print(f"SYNTHESIS ENGINE: {ticker}")
        print(f"{'='*80}\n")

        # Step 1: Get industry-specific weights
        weights = self._get_weights(sector, industry)
        print(f"Industry: {sector or 'Unknown'}")
        print(f"Weights: {weights}\n")

        # Step 2: Cross-layer structural reasoning
        structural_analysis = self._analyze_structural_patterns(layers)
        print("Structural Analysis:")
        for key, value in structural_analysis.items():
            if key == 'override_rules_triggered':
                if value:
                    print(f"  OVERRIDE RULES TRIGGERED:")
                    for rule in value:
                        print(f"    - {rule}")
            else:
                print(f"  {key}: {value}")

        # Step 3: Calculate weighted score
        weighted_score, score_breakdown = self._calculate_weighted_score(layers, weights)
        print(f"\nWeighted Score: {weighted_score:.1f}/100")
        print("Score Breakdown:")
        for layer, score_data in score_breakdown.items():
            print(f"  {layer}: {score_data['raw']:.1f} × {score_data['weight']:.1f} = {score_data['weighted']:.1f}")

        # Step 4: Bayesian belief state
        belief_state = self._compute_belief_state(layers, structural_analysis)
        print(f"\nBelief State:")
        print(f"  P(Structural Bull Case): {belief_state['bull_prob']:.1%}")
        print(f"  P(Structural Bear Case): {belief_state['bear_prob']:.1%}")
        print(f"  P(Distress Risk): {belief_state['distress_prob']:.1%}")

        # Step 5: Determine conviction and action
        conviction, action, reasoning = self._determine_action(
            weighted_score,
            structural_analysis,
            belief_state,
            layers
        )

        print(f"\nConviction: {conviction}")
        print(f"Action: {action}")
        print(f"Reasoning: {reasoning}\n")

        return {
            'ticker': ticker,
            'weighted_score': round(weighted_score, 2),
            'raw_score': sum(l.get('score', 5) for l in layers.values()),
            'conviction': conviction,
            'action': action,
            'reasoning': reasoning,
            'weights_used': weights,
            'score_breakdown': score_breakdown,
            'structural_analysis': structural_analysis,
            'belief_state': belief_state,
            'disqualified': structural_analysis.get('disqualify', False),
            'override_rules': structural_analysis.get('override_rules_triggered', [])
        }

    def _get_weights(self, sector: Optional[str], industry: Optional[str]) -> Dict[str, float]:
        """
        Get industry-specific weights

        Prefers industry, falls back to sector, then default
        """
        # Try industry first (more specific)
        if industry and industry in self.industry_weights:
            return {k: v for k, v in self.industry_weights[industry].items() if not k.startswith('_')}

        # Try sector
        if sector and sector in self.industry_weights:
            return {k: v for k, v in self.industry_weights[sector].items() if not k.startswith('_')}

        # Default
        return self.default_weights

    def _analyze_structural_patterns(self, layers: Dict[str, Dict]) -> Dict:
        """
        Cross-Layer Structural Reasoning

        This is where the magic happens. Layers inform each other.

        Override Rules (immediate disqualification):
        1. Financial distress + Management selling = AVOID
        2. Declining revenue + Deteriorating financials = SHORT_CANDIDATE
        3. Negative FCF + High debt = DISTRESS_RISK
        4. Competitive collapse + Margin compression = AVOID

        Amplification Rules (boost confidence):
        1. Strong business + Strong financials = High conviction
        2. Improving trajectory across all layers = Momentum play
        """
        analysis = {
            'disqualify': False,
            'amplify': False,
            'override_rules_triggered': [],
            'pattern_matches': [],
            'cross_layer_signals': {}
        }

        # Extract layer states
        business = layers.get('business_model', {})
        financial = layers.get('financial_truth', {})
        management = layers.get('management', {})
        competitive = layers.get('competitive', {})
        risk = layers.get('risk', {})

        # CRITICAL OVERRIDE RULES

        # Rule 1: Financial Distress + Insider Selling = AVOID
        if (financial.get('risk_level') in ['critical', 'high'] and
            'NEGATIVE_FREE_CASH_FLOW' in financial.get('risk_flags', [])):

            if 'INSIDER_HEAVY_SELLING' in management.get('risk_flags', []):
                analysis['disqualify'] = True
                analysis['override_rules_triggered'].append(
                    "FINANCIAL_DISTRESS + INSIDER_SELLING = Management bailing before bankruptcy"
                )

        # Rule 2: Declining Revenue + Deteriorating Cash = Terminal Decline
        if ('DECLINING_REVENUE' in business.get('risk_flags', []) and
            'REVENUE_UP_CASH_DOWN' in financial.get('risk_flags', [])):
            analysis['disqualify'] = True
            analysis['override_rules_triggered'].append(
                "DECLINING_REVENUE + CASH_FLOW_DETERIORATION = Business dying"
            )

        # Rule 3: Negative FCF + High Debt = Bankruptcy Risk
        if ('NEGATIVE_FREE_CASH_FLOW' in financial.get('risk_flags', []) and
            'HIGH_DEBT_TO_EBITDA' in financial.get('risk_flags', [])):
            analysis['disqualify'] = True
            analysis['override_rules_triggered'].append(
                "NEGATIVE_FCF + HIGH_DEBT = Cannot service debt, distress imminent"
            )

        # Rule 4: Low Interest Coverage + Rising Debt = Spiral
        if ('LOW_INTEREST_COVERAGE' in financial.get('risk_flags', []) and
            financial.get('trajectory') == 'deteriorating'):
            analysis['disqualify'] = True
            analysis['override_rules_triggered'].append(
                "LOW_COVERAGE + DETERIORATING = Death spiral beginning"
            )

        # Rule 5: Competitive Collapse + Margin Compression = Avoid
        if (competitive.get('risk_level') in ['high', 'critical'] and
            'LOW_MARGINS' in business.get('risk_flags', [])):
            analysis['override_rules_triggered'].append(
                "COMPETITIVE_PRESSURE + LOW_MARGINS = No moat, commodity pricing"
            )

        # AMPLIFICATION RULES (positive reinforcement)

        # Strong business model + Strong financials = High conviction
        if (business.get('score', 0) >= 7 and
            financial.get('score', 0) >= 7):
            analysis['amplify'] = True
            analysis['pattern_matches'].append('STRONG_FUNDAMENTALS')

        # Everything improving = Momentum
        trajectories = [layer.get('trajectory') for layer in layers.values()]
        improving_count = trajectories.count('improving')
        deteriorating_count = trajectories.count('deteriorating')

        if improving_count >= 3 and deteriorating_count == 0:
            analysis['amplify'] = True
            analysis['pattern_matches'].append('BROAD_IMPROVEMENT')

        # Strong moat + High margins + Growing = Compounder
        if (business.get('score', 0) >= 8 and
            financial.get('trajectory') == 'improving'):
            analysis['pattern_matches'].append('COMPOUNDER_PROFILE')

        # Cross-layer consistency check
        scores = [layer.get('score', 5) for layer in layers.values() if 'score' in layer]
        if scores:
            score_std = np.std(scores)
            if score_std < 2:  # Low variance = consistency
                analysis['cross_layer_signals']['consistency'] = 'HIGH'
            elif score_std > 4:  # High variance = conflict
                analysis['cross_layer_signals']['consistency'] = 'CONFLICTING'
                analysis['pattern_matches'].append('MIXED_SIGNALS')

        return analysis

    def _calculate_weighted_score(
        self,
        layers: Dict[str, Dict],
        weights: Dict[str, float]
    ) -> Tuple[float, Dict]:
        """
        Industry-weighted scoring

        Not all layers matter equally for all industries.
        Software: Business model matters 4x more than debt
        Banks: Balance sheet matters 4x more than competitive moat
        """
        weighted_total = 0
        weight_sum = 0
        breakdown = {}

        layer_mapping = {
            'business_model': 'business_model',
            'financial_truth': 'financial_truth',
            'management': 'management',
            'market_structure': 'market_structure',
            'competitive': 'competitive',
            'macro': 'macro',
            'risk': 'risk'
        }

        for layer_key, weight_key in layer_mapping.items():
            if layer_key in layers:
                layer_data = layers[layer_key]
                raw_score = layer_data.get('score', 5)
                weight = weights.get(weight_key, 1.0)

                weighted_score = raw_score * weight
                weighted_total += weighted_score
                weight_sum += weight

                breakdown[layer_key] = {
                    'raw': raw_score,
                    'weight': weight,
                    'weighted': weighted_score
                }

        # Normalize to 0-100 scale
        # Max possible = 10 * sum(weights)
        max_possible = 10 * weight_sum
        normalized_score = (weighted_total / max_possible) * 100 if max_possible > 0 else 50

        return normalized_score, breakdown

    def _compute_belief_state(
        self,
        layers: Dict[str, Dict],
        structural_analysis: Dict
    ) -> Dict:
        """
        Bayesian belief computation

        Instead of just scores, compute probabilities:
        - P(Structural Bull Case) = Long-term winner
        - P(Structural Bear Case) = Avoid or short
        - P(Distress) = Bankruptcy risk
        """
        # Start with priors (base rates)
        bull_prob = 0.3  # 30% of stocks are long-term winners
        bear_prob = 0.2  # 20% are structural shorts
        distress_prob = 0.05  # 5% face bankruptcy

        # Update based on layer evidence

        # Financial layer updates distress probability
        financial = layers.get('financial_truth', {})
        if financial.get('risk_level') == 'critical':
            distress_prob *= 5  # 25% distress risk
        elif financial.get('risk_level') == 'high':
            distress_prob *= 3  # 15% distress risk

        # Business model updates bull probability
        business = layers.get('business_model', {})
        if business.get('score', 5) >= 8:
            bull_prob *= 2  # 60% if strong business
        elif business.get('score', 5) <= 3:
            bull_prob *= 0.3  # 9% if weak business
            bear_prob *= 2  # 40% bear case

        # Trajectory matters
        trajectories = [layer.get('trajectory') for layer in layers.values()]
        improving_count = trajectories.count('improving')
        deteriorating_count = trajectories.count('deteriorating')

        if improving_count >= 3:
            bull_prob *= 1.5
        if deteriorating_count >= 3:
            bear_prob *= 2
            distress_prob *= 1.5

        # Structural overrides force probabilities
        if structural_analysis.get('disqualify'):
            bull_prob = 0.05
            bear_prob = 0.7
            distress_prob = min(distress_prob * 2, 0.5)

        # Normalize probabilities
        total = bull_prob + bear_prob + distress_prob
        if total > 1:
            bull_prob /= total
            bear_prob /= total
            distress_prob /= total

        return {
            'bull_prob': bull_prob,
            'bear_prob': bear_prob,
            'distress_prob': distress_prob,
            'neutral_prob': 1 - bull_prob - bear_prob - distress_prob
        }

    def _determine_action(
        self,
        weighted_score: float,
        structural_analysis: Dict,
        belief_state: Dict,
        layers: Dict
    ) -> Tuple[str, str, str]:
        """
        Determine conviction level and action

        Conviction Levels:
        - HIGH: High probability structural winner (bull_prob > 60%)
        - MEDIUM: Decent setup but not exceptional (score > 60)
        - LOW: Marginal, speculation only (score 40-60)
        - AVOID: Don't touch (score < 40 or override rules)
        - SHORT: Structural bear case (bear_prob > 50% or distress)

        Actions:
        - BUY_HIGH_CONVICTION: 6+ month hold, position size 5-10%
        - BUY_MEDIUM: 3-6 month, position size 2-5%
        - TRADE_ONLY: Weeks, position size <2%
        - AVOID: Don't trade
        - SHORT_CANDIDATE: Consider short
        """
        # Check for disqualification
        if structural_analysis.get('disqualify'):
            return (
                'AVOID',
                'DO_NOT_TRADE',
                f"Structural disqualifiers: {', '.join(structural_analysis['override_rules_triggered'])}"
            )

        # Check distress probability
        if belief_state['distress_prob'] > 0.2:
            return (
                'SHORT',
                'SHORT_CANDIDATE',
                f"High bankruptcy risk ({belief_state['distress_prob']:.0%})"
            )

        # Check bear probability
        if belief_state['bear_prob'] > 0.5:
            return (
                'SHORT',
                'SHORT_CANDIDATE',
                f"Structural bear case ({belief_state['bear_prob']:.0%} probability)"
            )

        # Bull cases
        if belief_state['bull_prob'] > 0.6 and weighted_score >= 70:
            reasoning = f"High conviction structural winner (P={belief_state['bull_prob']:.0%}, Score={weighted_score:.0f})"
            if structural_analysis.get('amplify'):
                reasoning += f" | Amplified by: {', '.join(structural_analysis['pattern_matches'])}"
            return ('HIGH', 'BUY_HIGH_CONVICTION', reasoning)

        if weighted_score >= 65:
            return (
                'MEDIUM',
                'BUY_MEDIUM',
                f"Solid setup (Score={weighted_score:.0f}, Bull P={belief_state['bull_prob']:.0%})"
            )

        if weighted_score >= 55:
            return (
                'LOW',
                'TRADE_ONLY',
                f"Marginal case (Score={weighted_score:.0f}), short-term only"
            )

        if weighted_score >= 40:
            return (
                'AVOID',
                'SPECULATION_ONLY',
                f"Weak case (Score={weighted_score:.0f}), too many red flags"
            )

        # Below 40 = avoid
        return (
            'AVOID',
            'DO_NOT_TRADE',
            f"Poor fundamentals (Score={weighted_score:.0f})"
        )


def main():
    """Test the synthesis engine"""
    from market_truth.core.layer_schema import LayerOutput

    # Mock layer outputs
    test_layers = {
        'business_model': LayerOutput.normalize({
            'score': 8,
            'red_flags': [],
            'green_flags': ['STRONG_REVENUE_GROWTH', 'EXCEPTIONAL_MARGINS']
        }),
        'financial_truth': LayerOutput.normalize({
            'score': 7,
            'red_flags': [],
            'green_flags': ['OCF_ACCELERATING', 'DEBT_FREE_OR_NET_CASH']
        }),
        'management': LayerOutput.normalize({
            'score': 6,
            'red_flags': [],
            'green_flags': ['INSIDER_BUYING']
        }),
        'competitive': LayerOutput.normalize({
            'score': 8,
            'red_flags': [],
            'green_flags': []
        })
    }

    engine = SynthesisEngine()
    result = engine.synthesize(
        layers=test_layers,
        ticker='TEST',
        sector='Technology',
        industry='Software'
    )

    print(f"\n{'='*80}")
    print(f"SYNTHESIS RESULT")
    print(f"{'='*80}\n")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
