"""
# FR-06, NFR-01: Central parameters for portfolio optimization experiments.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class OptimizationParams:
    """Parameters defining optimization constraints, data integrity and metaheuristic settings."""
    # Data & Integrity
    expected_sha256: str = "10d98d487cc565341296462c5cb29efa876e0dbf56cdcde46310aa73b21eaba8"
    drive_file_id: str = "1e_DRIVE_FILE_ID_PLACEHOLDER"
    
    # Portfolio Constraints
    cardinality_limit: int = 5
    min_weight: float = 0.05
    max_weight: float = 0.40
    target_daily_return: float = 0.0010  # ~0.10% daily (~36.5% annual)
    
    # Risk Metrics
    cvar_alpha: float = 0.95
    risk_aversion_lambda: float = 1.0
    
    # Genetic Algorithm Settings
    ga_seed: int = 42
    ga_pop_size: int = 100
    ga_generations: int = 80
    ga_cx_prob: float = 0.80
    ga_mut_prob: float = 0.20
    ga_tournament_size: int = 3
    ga_penalty_weight: float = 1000.0


# Default singleton instance
DEFAULT_PARAMS = OptimizationParams()
PARAMS = DEFAULT_PARAMS
