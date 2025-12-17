"""
Temporal Delta Engine
Tracks how analysis changes over time

Key Insight: The direction matters as much as the level.
- Score going from 6→8 = momentum
- Score going from 8→6 = deteriorating (sell signal)
- Red flags appearing = new risk emerging
- Red flags disappearing = recovery

Storage: cache/ticker_history/{ticker}.json
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TemporalEngine:
    """
    Tracks and analyzes changes in analysis over time

    Stores history of:
    - Layer scores
    - Risk flags
    - Trajectories
    - Synthesis results

    Computes:
    - Score momentum (accelerating/decelerating)
    - Risk drift (getting safer/riskier)
    - Trajectory consistency
    - Conviction changes
    """

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache" / "ticker_history"
        else:
            cache_dir = Path(cache_dir)

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save_analysis(
        self,
        ticker: str,
        analysis: Dict,
        synthesis: Dict
    ) -> None:
        """
        Save current analysis to history

        Args:
            ticker: Stock ticker
            analysis: Full analysis dict with all layers
            synthesis: Synthesis engine output
        """
        history_file = self.cache_dir / f"{ticker}.json"

        # Load existing history
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
        else:
            history = {
                'ticker': ticker,
                'first_analyzed': datetime.now().isoformat(),
                'analyses': []
            }

        # Create snapshot
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'layers': {},
            'synthesis': synthesis,
            'metadata': {
                'version': '2.0'  # Track schema version
            }
        }

        # Extract layer scores and flags
        for layer_name, layer_data in analysis.get('layers', {}).items():
            if isinstance(layer_data, dict):
                snapshot['layers'][layer_name] = {
                    'score': layer_data.get('score', 0),
                    'trajectory': layer_data.get('trajectory', 'unknown'),
                    'risk_flags': layer_data.get('risk_flags', []),
                    'strength_flags': layer_data.get('strength_flags', []),
                    'risk_level': layer_data.get('risk_level', 'unknown')
                }

        # Append to history
        history['analyses'].append(snapshot)
        history['last_updated'] = datetime.now().isoformat()

        # Save
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)

        print(f"[Temporal] Saved analysis snapshot for {ticker}")

    def get_temporal_analysis(self, ticker: str) -> Optional[Dict]:
        """
        Analyze changes over time for a ticker

        Returns:
            Dict with momentum, drift, and change analysis
            None if no history exists
        """
        history_file = self.cache_dir / f"{ticker}.json"

        if not history_file.exists():
            return None

        with open(history_file, 'r') as f:
            history = json.load(f)

        if len(history['analyses']) < 2:
            return {
                'note': 'Insufficient history (need 2+ analyses)',
                'analysis_count': len(history['analyses'])
            }

        # Get latest and previous
        latest = history['analyses'][-1]
        previous = history['analyses'][-2]

        return self._compute_deltas(latest, previous, history)

    def _compute_deltas(
        self,
        latest: Dict,
        previous: Dict,
        full_history: Dict
    ) -> Dict:
        """
        Compute changes between analyses

        Returns detailed delta analysis
        """
        deltas = {
            'timestamp_latest': latest['timestamp'],
            'timestamp_previous': previous['timestamp'],
            'layer_changes': {},
            'risk_drift': {},
            'conviction_change': {},
            'momentum': {},
            'summary': {}
        }

        # Layer-by-layer score changes
        latest_layers = latest.get('layers', {})
        previous_layers = previous.get('layers', {})

        score_changes = []
        for layer_name in latest_layers.keys():
            if layer_name in previous_layers:
                latest_score = latest_layers[layer_name].get('score', 0)
                previous_score = previous_layers[layer_name].get('score', 0)
                delta = latest_score - previous_score

                score_changes.append(delta)

                deltas['layer_changes'][layer_name] = {
                    'previous': previous_score,
                    'latest': latest_score,
                    'delta': round(delta, 2),
                    'direction': 'improving' if delta > 0 else 'deteriorating' if delta < 0 else 'stable',
                    'trajectory_previous': previous_layers[layer_name].get('trajectory', 'unknown'),
                    'trajectory_latest': latest_layers[layer_name].get('trajectory', 'unknown')
                }

        # Overall score momentum
        if score_changes:
            avg_delta = sum(score_changes) / len(score_changes)

            deltas['momentum'] = {
                'average_layer_delta': round(avg_delta, 2),
                'direction': 'IMPROVING' if avg_delta > 0.5 else 'DETERIORATING' if avg_delta < -0.5 else 'STABLE',
                'acceleration': 'ACCELERATING' if avg_delta > 1.0 else 'DECELERATING' if avg_delta < -1.0 else 'STEADY'
            }

        # Risk drift analysis
        risk_drift = self._analyze_risk_drift(latest_layers, previous_layers)
        deltas['risk_drift'] = risk_drift

        # Conviction changes
        latest_synth = latest.get('synthesis', {})
        previous_synth = previous.get('synthesis', {})

        if latest_synth and previous_synth:
            deltas['conviction_change'] = {
                'previous_conviction': previous_synth.get('conviction', 'UNKNOWN'),
                'latest_conviction': latest_synth.get('conviction', 'UNKNOWN'),
                'previous_action': previous_synth.get('action', 'UNKNOWN'),
                'latest_action': latest_synth.get('action', 'UNKNOWN'),
                'changed': latest_synth.get('conviction') != previous_synth.get('conviction')
            }

        # Summary interpretation
        deltas['summary'] = self._generate_summary(deltas)

        return deltas

    def _analyze_risk_drift(
        self,
        latest_layers: Dict,
        previous_layers: Dict
    ) -> Dict:
        """
        Analyze how risk profile is changing

        Key Questions:
        - Are new red flags appearing?
        - Are existing red flags disappearing?
        - Is risk level escalating?
        """
        drift = {
            'new_risks': [],
            'resolved_risks': [],
            'persistent_risks': [],
            'risk_level_change': {},
            'overall_drift': 'STABLE'
        }

        # Collect all risk flags
        all_latest_risks = set()
        all_previous_risks = set()

        for layer_name in latest_layers.keys():
            if layer_name in previous_layers:
                latest_flags = set(latest_layers[layer_name].get('risk_flags', []))
                previous_flags = set(previous_layers[layer_name].get('risk_flags', []))

                all_latest_risks.update(latest_flags)
                all_previous_risks.update(previous_flags)

                # Check risk level changes
                latest_risk_level = latest_layers[layer_name].get('risk_level', 'unknown')
                previous_risk_level = previous_layers[layer_name].get('risk_level', 'unknown')

                if latest_risk_level != previous_risk_level:
                    drift['risk_level_change'][layer_name] = {
                        'from': previous_risk_level,
                        'to': latest_risk_level
                    }

        # New risks (appeared since last analysis)
        drift['new_risks'] = list(all_latest_risks - all_previous_risks)

        # Resolved risks (were present, now gone)
        drift['resolved_risks'] = list(all_previous_risks - all_latest_risks)

        # Persistent risks (still present)
        drift['persistent_risks'] = list(all_latest_risks & all_previous_risks)

        # Overall drift
        if len(drift['new_risks']) > len(drift['resolved_risks']):
            drift['overall_drift'] = 'DETERIORATING'
        elif len(drift['resolved_risks']) > len(drift['new_risks']):
            drift['overall_drift'] = 'IMPROVING'
        elif len(drift['persistent_risks']) > 5:
            drift['overall_drift'] = 'PERSISTENTLY_RISKY'
        else:
            drift['overall_drift'] = 'STABLE'

        return drift

    def _generate_summary(self, deltas: Dict) -> Dict:
        """
        Generate human-readable summary of changes
        """
        momentum = deltas.get('momentum', {})
        risk_drift = deltas.get('risk_drift', {})
        conviction_change = deltas.get('conviction_change', {})

        summary = {
            'headline': '',
            'key_changes': [],
            'recommendation': ''
        }

        # Headline
        momentum_dir = momentum.get('direction', 'STABLE')
        risk_dir = risk_drift.get('overall_drift', 'STABLE')

        if momentum_dir == 'IMPROVING' and risk_dir in ['IMPROVING', 'STABLE']:
            summary['headline'] = "[^] IMPROVING: Fundamentals strengthening"
        elif momentum_dir == 'DETERIORATING' and risk_dir in ['DETERIORATING', 'PERSISTENTLY_RISKY']:
            summary['headline'] = "[v] DETERIORATING: Red flags multiplying"
        elif momentum_dir == 'STABLE' and risk_dir == 'STABLE':
            summary['headline'] = "[->] STABLE: No significant changes"
        else:
            summary['headline'] = "[!] MIXED: Conflicting signals"

        # Key changes
        if risk_drift.get('new_risks'):
            summary['key_changes'].append(f"New risks: {', '.join(risk_drift['new_risks'][:3])}")

        if risk_drift.get('resolved_risks'):
            summary['key_changes'].append(f"Resolved risks: {', '.join(risk_drift['resolved_risks'][:3])}")

        if conviction_change.get('changed'):
            summary['key_changes'].append(
                f"Conviction changed: {conviction_change['previous_conviction']} -> {conviction_change['latest_conviction']}"
            )

        # Recommendation
        if momentum_dir == 'IMPROVING':
            summary['recommendation'] = "Consider increasing position or initiating"
        elif momentum_dir == 'DETERIORATING':
            summary['recommendation'] = "Consider reducing position or exiting"
        else:
            summary['recommendation'] = "Hold current position, monitor closely"

        return summary

    def get_history_summary(self, ticker: str) -> Optional[Dict]:
        """
        Get summary statistics across all analyses
        """
        history_file = self.cache_dir / f"{ticker}.json"

        if not history_file.exists():
            return None

        with open(history_file, 'r') as f:
            history = json.load(f)

        analyses = history.get('analyses', [])

        if not analyses:
            return None

        # Extract score time series for each layer
        layer_series = {}

        for analysis in analyses:
            for layer_name, layer_data in analysis.get('layers', {}).items():
                if layer_name not in layer_series:
                    layer_series[layer_name] = []

                layer_series[layer_name].append({
                    'timestamp': analysis['timestamp'],
                    'score': layer_data.get('score', 0),
                    'trajectory': layer_data.get('trajectory', 'unknown')
                })

        return {
            'ticker': ticker,
            'first_analyzed': history.get('first_analyzed'),
            'last_updated': history.get('last_updated'),
            'analysis_count': len(analyses),
            'layer_series': layer_series
        }


def main():
    """Test temporal engine"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python temporal_engine.py <TICKER>")
        return

    ticker = sys.argv[1].upper()

    engine = TemporalEngine()

    # Get temporal analysis
    temporal = engine.get_temporal_analysis(ticker)

    if temporal is None:
        print(f"No history found for {ticker}")
        return

    print(f"\n{'='*80}")
    print(f"TEMPORAL ANALYSIS: {ticker}")
    print(f"{'='*80}\n")

    print(json.dumps(temporal, indent=2))


if __name__ == "__main__":
    main()
