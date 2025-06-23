"""Unit tests for NSE data fetching functionality."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.data_fetcher import NSEDataFetcher


class TestNSEDataFetcher:
    """Test suite for NSEDataFetcher class."""
    
    @pytest.fixture
    def fetcher(self) -> NSEDataFetcher:
        """Create NSE data fetcher instance."""
        return NSEDataFetcher()
    
    @pytest.fixture
    def mock_nse_response(self) -> Dict[str, Any]:
        """Create mock NSE API response."""
        return {
            "records": {
                "data": [
                    {
                        "strikePrice": 25000,
                        "expiryDate": "30-Jan-2025",
                        "CE": {
                            "openInterest": 1000,
                            "changeinOpenInterest": 100,
                            "lastPrice": 120.5,
                            "bidprice": 118.0,
                            "askPrice": 123.0,
                            "impliedVolatility": 15.2,
                            "underlyingValue": 25045.3
                        },
                        "PE": {
                            "openInterest": 800,
                            "changeinOpenInterest": -50,
                            "lastPrice": 75.2,
                            "bidprice": 73.0,
                            "askPrice": 77.4,
                            "impliedVolatility": 14.8,
                            "underlyingValue": 25045.3
                        }
                    },
                    {
                        "strikePrice": 25050,
                        "expiryDate": "30-Jan-2025",
                        "CE": {
                            "openInterest": 1500,
                            "changeinOpenInterest": 200,
                            "lastPrice": 95.3,
                            "bidprice": 93.0,
                            "askPrice": 97.5,
                            "impliedVolatility": 15.8,
                            "underlyingValue": 25045.3
                        },
                        "PE": {
                            "openInterest": 1200,
                            "changeinOpenInterest": 150,
                            "lastPrice": 98.7,
                            "bidprice": 96.2,
                            "askPrice": 101.2,
                            "impliedVolatility": 15.1,
                            "underlyingValue": 25045.3
                        }
                    }
                ]
            }
        }
    
    def test_fetcher_initialization(self, fetcher: NSEDataFetcher) -> None:
        """Test fetcher initialization."""
        assert fetcher.URL == 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
        assert 'user-agent' in fetcher.HEADERS
        assert fetcher.session is not None
    
    @patch('requests.Session.get')
    def test_fetch_option_chain_success(self, mock_get: Mock, fetcher: NSEDataFetcher, mock_nse_response: Dict[str, Any]) -> None:
        """Test successful option chain fetching."""
        # Mock the session requests
        mock_response = Mock()
        mock_response.json.return_value = mock_nse_response
        mock_response.cookies = {'session': 'test_cookie'}
        mock_get.return_value = mock_response
        
        result = fetcher.fetch_option_chain()
        
        assert result == mock_nse_response
        assert mock_get.call_count == 2  # Initial request + actual data request
    
    @patch('requests.Session.get')  
    def test_fetch_option_chain_network_error(self, mock_get: Mock, fetcher: NSEDataFetcher) -> None:
        """Test network error handling in option chain fetching."""
        mock_get.side_effect = ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            fetcher.fetch_option_chain()
    
    def test_parse_option_data_structure(self, fetcher: NSEDataFetcher) -> None:
        """Test option data parsing structure."""
        # Create simplified mock response that matches actual NSE format
        mock_response = {
            "records": {
                "data": [
                    [
                        25000,  # Strike price
                        "30-Jan-2025",  # Expiry
                        # ... other fields would be here in real data
                        {  # PE (Put) data
                            "openInterest": 800,
                            "changeinOpenInterest": -50,
                            "lastPrice": 75.2,
                            "bidprice": 73.0,
                            "askPrice": 77.4,
                            "impliedVolatility": 14.8,
                            "underlyingValue": 25045.3
                        },
                        {  # CE (Call) data  
                            "openInterest": 1000,
                            "changeinOpenInterest": 100,
                            "lastPrice": 120.5,
                            "bidprice": 118.0,
                            "askPrice": 123.0,
                            "impliedVolatility": 15.2,
                            "underlyingValue": 25045.3
                        }
                    ]
                ]
            }
        }
        
        optionchain, underlying_ltp = fetcher.parse_option_data(mock_response)
        
        # Test DataFrame structure
        assert isinstance(optionchain, pd.DataFrame)
        assert isinstance(underlying_ltp, float)
        
        expected_columns = [
            "Expiry", "Call OI", "Call C_OI", "Call IV", "Call Bid", "Call Ask", 
            "Call LTP", "Strike", "Put Bid", "Put Ask", "Put LTP", "Put IV", 
            "Put C_OI", "Put OI"
        ]
        
        for col in expected_columns:
            assert col in optionchain.columns
    
    def test_parse_option_data_with_zero_values(self, fetcher: NSEDataFetcher) -> None:
        """Test parsing with zero/missing option values."""
        mock_response = {
            "records": {
                "data": [
                    [
                        25000,
                        "30-Jan-2025",
                        {   # Put data with underlyingValue
                            "openInterest": 0,
                            "changeinOpenInterest": 0,
                            "lastPrice": 0,
                            "bidprice": 0,
                            "askPrice": 0,
                            "impliedVolatility": 0,
                            "underlyingValue": 25045.3
                        },
                        {   # Call data present
                            "openInterest": 1000,
                            "changeinOpenInterest": 100,
                            "lastPrice": 120.5,
                            "bidprice": 118.0,
                            "askPrice": 123.0,
                            "impliedVolatility": 15.2,
                            "underlyingValue": 25045.3
                        }
                    ]
                ]
            }
        }
        
        optionchain, underlying_ltp = fetcher.parse_option_data(mock_response)
        
        # Should handle zero put data gracefully
        assert len(optionchain) == 1
        assert optionchain.iloc[0]['Put OI'] == 0
        assert optionchain.iloc[0]['Put LTP'] == 0.0
        assert optionchain.iloc[0]['Call OI'] == 1000
        assert optionchain.iloc[0]['Call LTP'] == 120.5
    
    def test_parse_option_data_empty_response(self, fetcher: NSEDataFetcher) -> None:
        """Test parsing empty response.""" 
        mock_response = {
            "records": {
                "data": []
            }
        }
        
        with pytest.raises((IndexError, KeyError)):
            fetcher.parse_option_data(mock_response)
    
    def test_parse_option_data_data_types(self, fetcher: NSEDataFetcher) -> None:
        """Test correct data types in parsed DataFrame."""
        mock_response = {
            "records": {
                "data": [
                    [
                        25000,
                        "30-Jan-2025",
                        {
                            "openInterest": 800,
                            "changeinOpenInterest": -50,
                            "lastPrice": 75.2,
                            "bidprice": 73.0,
                            "askPrice": 77.4,
                            "impliedVolatility": 14.8,
                            "underlyingValue": 25045.3
                        },
                        {
                            "openInterest": 1000,
                            "changeinOpenInterest": 100,
                            "lastPrice": 120.5,
                            "bidprice": 118.0,
                            "askPrice": 123.0,
                            "impliedVolatility": 15.2,
                            "underlyingValue": 25045.3
                        }
                    ]
                ]
            }
        }
        
        optionchain, underlying_ltp = fetcher.parse_option_data(mock_response)
        
        # Test data types (numpy types are acceptable)
        assert isinstance(optionchain.iloc[0]['Strike'], (int, float, np.integer, np.floating))
        assert isinstance(optionchain.iloc[0]['Call OI'], (int, np.integer))
        assert isinstance(optionchain.iloc[0]['Put OI'], (int, np.integer))
        assert isinstance(optionchain.iloc[0]['Call LTP'], (float, np.floating))
        assert isinstance(optionchain.iloc[0]['Put LTP'], (float, np.floating))
        assert isinstance(underlying_ltp, (float, np.floating))
    
    def test_headers_configuration(self, fetcher: NSEDataFetcher) -> None:
        """Test that headers are properly configured for NSE requests."""
        headers = fetcher.HEADERS
        
        assert 'user-agent' in headers
        assert 'Mozilla' in headers['user-agent']
        assert 'accept-encoding' in headers
        assert 'accept-language' in headers
        
        # Headers should mimic browser requests
        assert 'Chrome' in headers['user-agent'] or 'Firefox' in headers['user-agent']