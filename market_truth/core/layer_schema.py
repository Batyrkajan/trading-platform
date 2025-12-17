"""
Standardized Layer Output Schema
All analyzers must return this exact structure for cross-layer reasoning
"""
from typing import Dict, List, Literal
from datetime import datetime

# Type definitions
Trajectory = Literal["improving", "deteriorating", "stable", "unknown"]
RiskLevel = Literal["critical", "high", "medium", "low", "minimal"]


class LayerOutput:
    """
    Standard output format for all layer analyzers

    This enables:
    - Cross-layer inference (e.g., "financial weak" + "management selling" = avoid)
    - Bayesian belief updates (not just score summing)
    - Temporal tracking (score momentum matters)
    - Industry-specific weighting
    """

    @staticmethod
    def normalize(raw_output: Dict) -> Dict:
        """
        Convert legacy analyzer output to standardized format

        Args:
            raw_output: Old-style {'score': X, 'red_flags': [...], ...}

        Returns:
            Standardized LayerOutput dict
        """
        # Extract score (0-10)
        score = raw_output.get('score', 5)

        # Determine trajectory from flags
        red_flags = raw_output.get('red_flags', [])
        green_flags = raw_output.get('green_flags', [])

        if len(green_flags) > len(red_flags) * 1.5:
            trajectory = "improving"
        elif len(red_flags) > len(green_flags) * 1.5:
            trajectory = "deteriorating"
        elif score > 0:
            trajectory = "stable"
        else:
            trajectory = "unknown"

        # Risk flags to risk level
        critical_flags = [
            'NEGATIVE_FREE_CASH_FLOW',
            'LOW_INTEREST_COVERAGE',
            'REVENUE_UP_CASH_DOWN',
            'DECLINING_REVENUE',
            'BANKRUPTCY_RISK'
        ]

        high_risk_flags = [
            'HIGH_DEBT_TO_EBITDA',
            'SLOW_COLLECTIONS',
            'INVENTORY_BUILDING',
            'INSIDER_HEAVY_SELLING'
        ]

        risk_level = "minimal"
        for flag in red_flags:
            if flag in critical_flags:
                risk_level = "critical"
                break
            elif flag in high_risk_flags:
                risk_level = "high"

        if risk_level == "minimal" and len(red_flags) > 3:
            risk_level = "medium"
        elif risk_level == "minimal" and len(red_flags) > 0:
            risk_level = "low"

        # Extract core signals (layer-specific data)
        core_signals = {k: v for k, v in raw_output.items()
                       if k not in ['score', 'red_flags', 'green_flags', 'timestamp', 'ticker', 'error']}

        return {
            "score": score,
            "normalized_score": round(score / 10, 2),  # 0-1 scale for Bayesian
            "trajectory": trajectory,
            "risk_level": risk_level,
            "risk_flags": red_flags,
            "strength_flags": green_flags,
            "core_signals": core_signals,
            "raw_data": raw_output  # Keep original for debugging
        }

    @staticmethod
    def create_empty(reason: str = "No data") -> Dict:
        """Create neutral/empty layer output"""
        return {
            "score": 5,
            "normalized_score": 0.5,
            "trajectory": "unknown",
            "risk_level": "medium",
            "risk_flags": [],
            "strength_flags": [],
            "core_signals": {"note": reason},
            "raw_data": {}
        }
