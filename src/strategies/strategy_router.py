"""
Strategy Router (Factory)
--------------------------
This is the central place that picks the right routing strategy
based on the configuration. It maps strategy names to their
implementation modules.

If an unknown strategy name is given, it falls back to priority-based routing.
"""

from src.strategies import priority_strategy
from src.strategies import weighted_strategy
from src.strategies import lowest_latency_strategy
from src.strategies import lowest_cost_strategy
from src.strategies import round_robin_strategy
from src.strategies import health_based_strategy
from src.strategies import feature_based_strategy
from src.strategies import failover_strategy


# map of strategy names to their modules
STRATEGY_MAP = {
    "priority": priority_strategy,
    "weighted": weighted_strategy,
    "lowest-latency": lowest_latency_strategy,
    "lowest_latency": lowest_latency_strategy,
    "lowest-cost": lowest_cost_strategy,
    "lowest_cost": lowest_cost_strategy,
    "round-robin": round_robin_strategy,
    "round_robin": round_robin_strategy,
    "health-based": health_based_strategy,
    "health_based": health_based_strategy,
    "feature-based": feature_based_strategy,
    "feature_based": feature_based_strategy,
    "failover": failover_strategy,
}

# default strategy if none specified or if an invalid one is given
DEFAULT_STRATEGY = "priority"


def get_strategy(strategy_name):
    """
    Get the strategy module for the given strategy name.
    
    Args:
        strategy_name: string name of the strategy (e.g., "weighted", "priority")
    
    Returns:
        tuple of (strategy_module, actual_strategy_name)
    """
    if not strategy_name:
        strategy_name = DEFAULT_STRATEGY

    # normalize: lowercase and strip whitespace
    strategy_name = strategy_name.lower().strip()

    strategy = STRATEGY_MAP.get(strategy_name)

    if strategy is None:
        # unknown strategy, fall back to priority
        print(f"[WARNING] Unknown strategy '{strategy_name}', falling back to '{DEFAULT_STRATEGY}'")
        return STRATEGY_MAP[DEFAULT_STRATEGY], DEFAULT_STRATEGY

    return strategy, strategy_name


def get_available_strategies():
    """Return list of all supported strategy names (deduplicated)."""
    seen = set()
    unique = []
    for name, module in STRATEGY_MAP.items():
        if module not in seen:
            seen.add(module)
            unique.append(name)
    return unique
