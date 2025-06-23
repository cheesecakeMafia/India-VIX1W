"""Shared pytest fixtures and configuration."""


import pandas as pd
import pytest


@pytest.fixture
def sample_strikes() -> pd.Series:
    """Standard NIFTY strike prices for testing."""
    return pd.Series([24900, 24950, 25000, 25050, 25100, 25150])


@pytest.fixture
def sample_underlying_price() -> float:
    """Standard underlying price for testing."""
    return 25045.3


@pytest.fixture
def sample_risk_free_rate() -> float:
    """Standard risk-free rate for testing."""
    return 0.075


@pytest.fixture
def sample_time_to_expiries() -> dict[str, float]:
    """Standard time to expiry values for testing."""
    return {
        "near": 0.019,  # ~1 week
        "far": 0.038,  # ~2 weeks
    }


@pytest.fixture
def minimal_option_data() -> pd.DataFrame:
    """Minimal valid option chain data for basic testing."""
    return pd.DataFrame(
        {
            "Expiry": ["30-Jan-2025", "30-Jan-2025", "06-Feb-2025", "06-Feb-2025"],
            "Strike": [25000, 25050, 25000, 25050],
            "Call LTP": [120.5, 95.3, 140.2, 115.8],
            "Put LTP": [75.2, 98.7, 85.3, 108.9],
            "Call Bid": [118.0, 93.0, 138.0, 113.0],
            "Call Ask": [123.0, 97.5, 142.4, 118.6],
            "Put Bid": [73.0, 96.2, 83.0, 106.4],
            "Put Ask": [77.4, 101.2, 87.6, 111.4],
            "Call OI": [1000, 1500, 1200, 900],
            "Put OI": [800, 1200, 1000, 1100],
            "Call C_OI": [100, 200, 120, 90],
            "Put C_OI": [-50, 150, 80, 110],
            "Call IV": [15.2, 15.8, 16.1, 16.3],
            "Put IV": [14.8, 15.1, 15.9, 16.0],
        }
    )
