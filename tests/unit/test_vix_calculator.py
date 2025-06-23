"""Unit tests for VIX calculation functions."""

import math
from datetime import datetime, timedelta

import pandas as pd
import pytest

from src.vix_calculator import VIXCalculator


class TestVIXCalculator:
    """Test suite for VIXCalculator class."""

    @pytest.fixture
    def calculator(self) -> VIXCalculator:
        """Create VIX calculator instance."""
        return VIXCalculator(risk_free_rate=0.075, delta_k=50)

    @pytest.fixture
    def sample_option_data(self) -> pd.DataFrame:
        """Create sample option chain data for testing."""
        return pd.DataFrame(
            {
                "Expiry": ["2025-01-30", "2025-01-30", "2025-01-30", "2025-02-06", "2025-02-06"],
                "Strike": [25000, 25050, 25100, 25000, 25050],
                "Call LTP": [120.5, 95.3, 72.1, 140.2, 115.8],
                "Put LTP": [75.2, 98.7, 125.4, 85.3, 108.9],
                "Call Bid": [118.0, 93.0, 70.0, 138.0, 113.0],
                "Call Ask": [123.0, 97.5, 74.2, 142.4, 118.6],
                "Put Bid": [73.0, 96.2, 123.0, 83.0, 106.4],
                "Put Ask": [77.4, 101.2, 127.8, 87.6, 111.4],
                "Call OI": [1000, 1500, 800, 1200, 900],
                "Put OI": [800, 1200, 1600, 1000, 1100],
            }
        )

    def test_get_atm_strike_exact_match(self, calculator: VIXCalculator) -> None:
        """Test ATM strike calculation with exact price match."""
        strikes = pd.Series([24950, 25000, 25050, 25100])
        underlying = 25000.0

        atm = calculator.get_atm_strike(strikes, underlying)

        assert atm == 25000.0

    def test_get_atm_strike_closest_match(self, calculator: VIXCalculator) -> None:
        """Test ATM strike calculation with closest price match."""
        strikes = pd.Series([24950, 25000, 25050, 25100])
        underlying = 25025.0

        atm = calculator.get_atm_strike(strikes, underlying)

        assert atm == 25000.0  # Closer to 25000 than 25050

    @pytest.mark.parametrize(
        "underlying,expected",
        [
            (
                24975.0,
                24950.0,
            ),  # Closer to 24950 (25 away) than 25000 (25 away) - first in list wins
            (25025.0, 25000.0),
            (25075.0, 25050.0),
            (25125.0, 25100.0),
        ],
    )
    def test_get_atm_strike_various_prices(
        self, calculator: VIXCalculator, underlying: float, expected: float
    ) -> None:
        """Test ATM strike calculation with various underlying prices."""
        strikes = pd.Series([24950, 25000, 25050, 25100])

        atm = calculator.get_atm_strike(strikes, underlying)

        assert atm == expected

    def test_calculate_time_to_expiry_future_date(self, calculator: VIXCalculator) -> None:
        """Test time to expiry calculation for future date."""
        future_date = datetime.now() + timedelta(days=7, hours=3, minutes=30)

        time_to_expiry = calculator.calculate_time_to_expiry(future_date)

        # Should be approximately 7 days = 0.0191 years
        assert 0.019 < time_to_expiry < 0.021

    def test_calculate_time_to_expiry_precision(self, calculator: VIXCalculator) -> None:
        """Test time to expiry calculation precision."""
        # Exactly 1 week from now
        future_date = datetime.now() + timedelta(weeks=1)

        time_to_expiry = calculator.calculate_time_to_expiry(future_date)
        expected = (7 * 1440) / 525_600  # 7 days in minutes / minutes per year

        assert abs(time_to_expiry - expected) < 0.001

    def test_organize_by_expiry_basic(
        self, calculator: VIXCalculator, sample_option_data: pd.DataFrame
    ) -> None:
        """Test basic expiry organization functionality."""
        organized = calculator.organize_by_expiry(sample_option_data, cutoff=50)

        assert len(organized) == 2  # Two unique expiry dates
        assert 0 in organized and 1 in organized
        assert "Expiry" not in organized[0].columns  # Should be dropped

    def test_organize_by_expiry_filtering(self, calculator: VIXCalculator) -> None:
        """Test OI and LTP filtering in expiry organization."""
        test_data = pd.DataFrame(
            {
                "Expiry": ["2025-01-30", "2025-01-30"],
                "Strike": [25000, 25050],
                "Call LTP": [0, 95.3],  # First row has zero LTP
                "Put LTP": [75.2, 98.7],
                "Call Bid": [118.0, 93.0],
                "Call Ask": [123.0, 97.5],
                "Put Bid": [73.0, 96.2],
                "Put Ask": [77.4, 101.2],
                "Call OI": [1000, 1500],
                "Put OI": [800, 1200],
            }
        )

        organized = calculator.organize_by_expiry(test_data, cutoff=50)

        # Should filter out row with zero LTP
        assert len(organized[0]) == 1
        assert organized[0].iloc[0]["Strike"] == 25050

    def test_calculate_vix_variables_forward_price(self, calculator: VIXCalculator) -> None:
        """Test forward price calculation in VIX variables."""
        test_df = pd.DataFrame(
            {
                "Strike": [25000],
                "Call LTP": [120.5],
                "Put LTP": [75.2],
                "Call Bid": [118.0],
                "Call Ask": [123.0],
                "Put Bid": [73.0],
                "Put Ask": [77.4],
            }
        )

        result = calculator.calculate_vix_variables(test_df, 0.019, 25000)

        # F = K + (C - P) * e^(r*T)
        expected_f = 25000 + (120.5 - 75.2) * math.exp(0.075 * 0.019)
        assert abs(result.iloc[0]["F"] - expected_f) < 0.01

    def test_calculate_vix_variables_spreads(self, calculator: VIXCalculator) -> None:
        """Test bid-ask spread calculations."""
        test_df = pd.DataFrame(
            {
                "Strike": [25000],
                "Call LTP": [120.5],
                "Put LTP": [75.2],
                "Call Bid": [118.0],
                "Call Ask": [122.0],  # 4 point spread
                "Put Bid": [74.0],
                "Put Ask": [76.0],  # 2 point spread
            }
        )

        result = calculator.calculate_vix_variables(test_df, 0.019, 25000)

        # Call spread = (Ask - Bid) * 200 / (Ask + Bid)
        expected_call_spread = (122.0 - 118.0) * 200 / (122.0 + 118.0)
        expected_put_spread = (76.0 - 74.0) * 200 / (76.0 + 74.0)

        assert abs(result.iloc[0]["Call Spread"] - expected_call_spread) < 0.01
        assert abs(result.iloc[0]["Put Spread"] - expected_put_spread) < 0.01

    def test_calculate_sigma_basic(self, calculator: VIXCalculator) -> None:
        """Test basic sigma calculation."""
        test_df = pd.DataFrame(
            {
                "A": [0.0001, 0.0002, 0.0001]  # Sample A values
            }
        )

        time_to_expiry = 0.019
        forward_price = 25045.3
        atm_strike = 25000.0

        sigma = calculator.calculate_sigma(test_df, time_to_expiry, forward_price, atm_strike)

        # Sigma should be positive
        assert sigma > 0
        # Should be reasonable volatility value (not extreme)
        assert 0.001 < sigma < 2.0

    def test_interpolate_vix_basic(self, calculator: VIXCalculator) -> None:
        """Test VIX interpolation between two sigmas."""
        sigma_1 = 0.15  # 15% volatility
        sigma_2 = 0.18  # 18% volatility
        T_1 = 0.019  # ~1 week
        T_2 = 0.038  # ~2 weeks

        vix = calculator.interpolate_vix(sigma_1, sigma_2, T_1, T_2)

        # VIX should be positive and reasonable
        assert vix > 0

    def test_interpolate_vix_edge_cases(self, calculator: VIXCalculator) -> None:
        """Test VIX interpolation edge cases."""
        # Same sigma values
        sigma = 0.12
        vix = calculator.interpolate_vix(sigma, sigma, 0.019, 0.038)

        # Should be positive
        assert vix > 0

    def test_calculator_initialization(self) -> None:
        """Test VIX calculator initialization with custom parameters."""
        custom_calc = VIXCalculator(risk_free_rate=0.05, delta_k=25)

        assert custom_calc.risk_free_rate == 0.05
        assert custom_calc.delta_k == 25

    def test_calculator_default_initialization(self) -> None:
        """Test VIX calculator with default parameters."""
        calc = VIXCalculator()

        assert calc.risk_free_rate == 0.075
        assert calc.delta_k == 50
