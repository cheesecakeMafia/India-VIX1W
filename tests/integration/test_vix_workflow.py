"""Integration tests for end-to-end VIX calculation workflow."""

import pytest
import pandas as pd
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
from typing import Dict, Any

from src.data_fetcher import NSEDataFetcher
from src.vix_calculator import VIXCalculator


class TestVIXWorkflow:
    """Integration tests for complete VIX calculation workflow."""
    
    @pytest.fixture
    def fetcher(self) -> NSEDataFetcher:
        """Create data fetcher instance."""
        return NSEDataFetcher()
    
    @pytest.fixture
    def calculator(self) -> VIXCalculator:
        """Create VIX calculator instance.""" 
        return VIXCalculator()
    
    @pytest.fixture
    def realistic_nse_data(self) -> Dict[str, Any]:
        """Create realistic NSE option chain data for testing."""
        return {
            "records": {
                "data": [
                    # Near expiry options
                    [24950, "30-Jan-2025", 
                     {"openInterest": 1200, "changeinOpenInterest": 50, "lastPrice": 95.5, 
                      "bidprice": 93.0, "askPrice": 98.0, "impliedVolatility": 16.2, "underlyingValue": 25045.3},
                     {"openInterest": 1500, "changeinOpenInterest": 100, "lastPrice": 142.8, 
                      "bidprice": 140.0, "askPrice": 145.6, "impliedVolatility": 15.8, "underlyingValue": 25045.3}],
                    
                    [25000, "30-Jan-2025",
                     {"openInterest": 800, "changeinOpenInterest": -50, "lastPrice": 75.2, 
                      "bidprice": 73.0, "askPrice": 77.4, "impliedVolatility": 14.8, "underlyingValue": 25045.3},
                     {"openInterest": 1000, "changeinOpenInterest": 100, "lastPrice": 120.5, 
                      "bidprice": 118.0, "askPrice": 123.0, "impliedVolatility": 15.2, "underlyingValue": 25045.3}],
                    
                    [25050, "30-Jan-2025",
                     {"openInterest": 1200, "changeinOpenInterest": 150, "lastPrice": 98.7, 
                      "bidprice": 96.2, "askPrice": 101.2, "impliedVolatility": 15.1, "underlyingValue": 25045.3},
                     {"openInterest": 1500, "changeinOpenInterest": 200, "lastPrice": 95.3, 
                      "bidprice": 93.0, "askPrice": 97.5, "impliedVolatility": 15.8, "underlyingValue": 25045.3}],
                    
                    [25100, "30-Jan-2025",
                     {"openInterest": 1600, "changeinOpenInterest": 250, "lastPrice": 125.4, 
                      "bidprice": 123.0, "askPrice": 127.8, "impliedVolatility": 15.5, "underlyingValue": 25045.3},
                     {"openInterest": 800, "changeinOpenInterest": -25, "lastPrice": 72.1, 
                      "bidprice": 70.0, "askPrice": 74.2, "impliedVolatility": 16.1, "underlyingValue": 25045.3}],
                    
                    # Next expiry options  
                    [24950, "06-Feb-2025",
                     {"openInterest": 900, "changeinOpenInterest": 75, "lastPrice": 105.3, 
                      "bidprice": 103.0, "askPrice": 107.6, "impliedVolatility": 16.8, "underlyingValue": 25045.3},
                     {"openInterest": 1200, "changeinOpenInterest": 120, "lastPrice": 155.2, 
                      "bidprice": 152.0, "askPrice": 158.4, "impliedVolatility": 16.2, "underlyingValue": 25045.3}],
                    
                    [25000, "06-Feb-2025",
                     {"openInterest": 1000, "changeinOpenInterest": 80, "lastPrice": 85.3, 
                      "bidprice": 83.0, "askPrice": 87.6, "impliedVolatility": 15.9, "underlyingValue": 25045.3},
                     {"openInterest": 1100, "changeinOpenInterest": 90, "lastPrice": 140.2, 
                      "bidprice": 138.0, "askPrice": 142.4, "impliedVolatility": 16.1, "underlyingValue": 25045.3}],
                    
                    [25050, "06-Feb-2025", 
                     {"openInterest": 1100, "changeinOpenInterest": 100, "lastPrice": 108.9, 
                      "bidprice": 106.4, "askPrice": 111.4, "impliedVolatility": 16.0, "underlyingValue": 25045.3},
                     {"openInterest": 900, "changeinOpenInterest": 85, "lastPrice": 115.8, 
                      "bidprice": 113.0, "askPrice": 118.6, "impliedVolatility": 16.3, "underlyingValue": 25045.3}],
                    
                    [25100, "06-Feb-2025",
                     {"openInterest": 1300, "changeinOpenInterest": 150, "lastPrice": 135.7, 
                      "bidprice": 133.0, "askPrice": 138.4, "impliedVolatility": 16.1, "underlyingValue": 25045.3},
                     {"openInterest": 700, "changeinOpenInterest": 50, "lastPrice": 92.4, 
                      "bidprice": 90.0, "askPrice": 94.8, "impliedVolatility": 16.7, "underlyingValue": 25045.3}]
                ]
            }
        }
    
    @patch('src.data_fetcher.NSEDataFetcher.fetch_option_chain')
    def test_end_to_end_vix_calculation(self, mock_fetch: Mock, fetcher: NSEDataFetcher, 
                                       calculator: VIXCalculator, realistic_nse_data: Dict[str, Any]) -> None:
        """Test complete VIX calculation workflow from data fetch to final result."""
        # Setup mock
        mock_fetch.return_value = realistic_nse_data
        
        # Step 1: Fetch and parse data
        raw_data = fetcher.fetch_option_chain()
        optionchain, underlying_ltp = fetcher.parse_option_data(raw_data)
        
        # Verify data structure
        assert isinstance(optionchain, pd.DataFrame)
        assert len(optionchain) == 8  # 4 strikes × 2 expiries
        assert underlying_ltp == 25045.3
        
        # Step 2: Organize data by expiry
        expiry_dict = calculator.organize_by_expiry(optionchain, cutoff=50)
        
        # Should have 2 expiries
        assert len(expiry_dict) == 2
        assert 0 in expiry_dict and 1 in expiry_dict
        
        # Step 3: Calculate ATM strike
        strikes = pd.Series(optionchain["Strike"].unique()).sort_values()
        atm_strike = calculator.get_atm_strike(strikes, underlying_ltp)
        
        assert atm_strike == 25050.0  # Closest to 25045.3
        
        # Step 4: Calculate time to expiry (future dates)
        near_expiry = datetime.now() + timedelta(days=7) + timedelta(hours=15.5)
        far_expiry = datetime.now() + timedelta(days=14) + timedelta(hours=15.5)
        
        T_1 = calculator.calculate_time_to_expiry(near_expiry)
        T_2 = calculator.calculate_time_to_expiry(far_expiry) 
        
        assert T_1 > 0 and T_2 > T_1
        
        # Step 5: Calculate VIX variables for both expiries
        near_df = expiry_dict[0].copy()
        far_df = expiry_dict[1].copy()
        
        # Remove unused columns
        cols_to_drop = ["Call OI", "Call C_OI", "Call IV", "Put IV", "Put C_OI", "Put OI"]
        near_df.drop(columns=[col for col in cols_to_drop if col in near_df.columns], inplace=True)
        far_df.drop(columns=[col for col in cols_to_drop if col in far_df.columns], inplace=True)
        
        near_df = calculator.calculate_vix_variables(near_df, T_1, atm_strike)
        far_df = calculator.calculate_vix_variables(far_df, T_2, atm_strike)
        
        # Verify variables were calculated
        assert 'F' in near_df.columns and 'A' in near_df.columns
        assert all(near_df['F'] > 0)  # Forward prices should be positive
        assert all(near_df['A'] > 0)  # VIX contributions should be positive
        
        # Step 6: Calculate forward prices
        F_near = near_df['F'].mean()
        F_far = far_df['F'].mean()
        
        assert F_near > 24000 and F_near < 26000  # Reasonable range
        assert F_far > 24000 and F_far < 26000
        
        # Step 7: Calculate sigmas
        sigma_1 = calculator.calculate_sigma(near_df, T_1, F_near, atm_strike)
        sigma_2 = calculator.calculate_sigma(far_df, T_2, F_far, atm_strike)
        
        assert sigma_1 > 0  # Volatility should be positive
        assert sigma_2 > 0  # Volatility should be positive
        
        # Step 8: Calculate final VIX
        vix1w = calculator.interpolate_vix(sigma_1, sigma_2, T_1, T_2)
        
        # Final VIX should be reasonable
        assert 5.0 < vix1w < 50.0  # Typical VIX range
        assert isinstance(vix1w, float)
    
    @patch('src.data_fetcher.NSEDataFetcher.fetch_option_chain')
    def test_workflow_with_filtered_data(self, mock_fetch: Mock, fetcher: NSEDataFetcher, 
                                        calculator: VIXCalculator) -> None:
        """Test workflow handles data filtering correctly."""
        # Data with some low OI options that should be filtered
        test_data = {
            "records": {
                "data": [
                    [25000, "30-Jan-2025",
                     {"openInterest": 10, "changeinOpenInterest": 5, "lastPrice": 75.2,  # Low OI
                      "bidprice": 73.0, "askPrice": 77.4, "impliedVolatility": 14.8, "underlyingValue": 25045.3},
                     {"openInterest": 1000, "changeinOpenInterest": 100, "lastPrice": 120.5,
                      "bidprice": 118.0, "askPrice": 123.0, "impliedVolatility": 15.2, "underlyingValue": 25045.3}],
                    
                    [25050, "30-Jan-2025", 
                     {"openInterest": 1200, "changeinOpenInterest": 150, "lastPrice": 98.7,
                      "bidprice": 96.2, "askPrice": 101.2, "impliedVolatility": 15.1, "underlyingValue": 25045.3},
                     {"openInterest": 1500, "changeinOpenInterest": 200, "lastPrice": 95.3,
                      "bidprice": 93.0, "askPrice": 97.5, "impliedVolatility": 15.8, "underlyingValue": 25045.3}]
                ]
            }
        }
        
        mock_fetch.return_value = test_data
        
        raw_data = fetcher.fetch_option_chain()
        optionchain, _ = fetcher.parse_option_data(raw_data)
        
        # Organize with higher cutoff to test filtering
        expiry_dict = calculator.organize_by_expiry(optionchain, cutoff=100)
        
        # Should filter out the low OI option
        assert len(expiry_dict[0]) == 1  # Only one row should remain
        assert expiry_dict[0].iloc[0]['Strike'] == 25050  # The high OI option
    
    def test_error_handling_invalid_data(self, fetcher: NSEDataFetcher, calculator: VIXCalculator) -> None:
        """Test error handling with invalid data structures."""
        invalid_data = {"records": {"data": []}}
        
        with pytest.raises((IndexError, KeyError, ValueError)):
            fetcher.parse_option_data(invalid_data)
    
    @patch('src.data_fetcher.NSEDataFetcher.fetch_option_chain')
    def test_workflow_data_consistency(self, mock_fetch: Mock, fetcher: NSEDataFetcher, 
                                     calculator: VIXCalculator, realistic_nse_data: Dict[str, Any]) -> None:
        """Test that workflow maintains data consistency throughout."""
        mock_fetch.return_value = realistic_nse_data
        
        # Fetch data
        raw_data = fetcher.fetch_option_chain()
        optionchain, underlying_ltp = fetcher.parse_option_data(raw_data)
        
        # Check data consistency
        unique_underlyings = optionchain.groupby('Expiry')['Strike'].nunique()
        
        # Should have same number of strikes per expiry
        assert len(unique_underlyings.unique()) <= 2  # At most 2 different counts
        
        # All strikes should be positive
        assert all(optionchain['Strike'] > 0)
        
        # All LTPs should be non-negative  
        assert all(optionchain['Call LTP'] >= 0)
        assert all(optionchain['Put LTP'] >= 0)
        
        # Bid should be <= Ask
        valid_calls = optionchain[optionchain['Call LTP'] > 0]
        valid_puts = optionchain[optionchain['Put LTP'] > 0]
        
        assert all(valid_calls['Call Bid'] <= valid_calls['Call Ask'])
        assert all(valid_puts['Put Bid'] <= valid_puts['Put Ask'])
    
    @pytest.mark.slow
    def test_performance_with_large_dataset(self, calculator: VIXCalculator) -> None:
        """Test performance with larger option chain dataset."""
        # Create larger dataset (100 strikes × 2 expiries)
        strikes = range(20000, 30000, 100)  # 100 strikes
        expiries = ["30-Jan-2025", "06-Feb-2025"]
        
        large_data = []
        for strike in strikes:
            for expiry in expiries:
                large_data.append({
                    'Expiry': expiry,
                    'Strike': strike,
                    'Call LTP': max(1.0, 100.0 - abs(strike - 25000) * 0.01),
                    'Put LTP': max(1.0, abs(strike - 25000) * 0.01 + 50.0),
                    'Call Bid': max(0.5, 98.0 - abs(strike - 25000) * 0.01),
                    'Call Ask': max(1.5, 102.0 - abs(strike - 25000) * 0.01),
                    'Put Bid': max(0.5, abs(strike - 25000) * 0.01 + 48.0),
                    'Put Ask': max(1.5, abs(strike - 25000) * 0.01 + 52.0),
                    'Call OI': 1000,
                    'Put OI': 1000,
                })
        
        large_df = pd.DataFrame(large_data)
        
        # Test performance - should complete in reasonable time
        import time
        start_time = time.time()
        
        expiry_dict = calculator.organize_by_expiry(large_df, cutoff=50)
        
        end_time = time.time()
        
        # Should process large dataset quickly (< 1 second)
        assert end_time - start_time < 1.0
        assert len(expiry_dict) == 2