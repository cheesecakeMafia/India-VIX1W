# ⚠️ ARCHIVED - India VIX1W - Weekly Volatility Index Calculator

> **🚨 This project is archived and no longer maintained. The code is provided as-is for reference purposes only.**

[![Status](https://img.shields.io/badge/status-archived-red.svg)]()
[![Maintenance](https://img.shields.io/badge/maintained-no-red.svg)]()
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-30%20passing-green.svg)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](./htmlcov/)

**⚠️ DEPRECATION NOTICE:** This repository has been archived and is no longer actively maintained. While the code may still function, it is not receiving updates, bug fixes, or security patches. Use at your own risk.

---

A modern Python implementation of weekly VIX calculation for India NIFTY options, implementing methodologies from NSE India VIX and CBOE VIX white papers to generate volatility index on weekly expiries rather than the standard monthly methodology.

## 📦 Archive Information

**Last Active**: This project was last actively developed in 2024.

**Reason for Archival**: This was a research project that has served its purpose. The codebase demonstrates VIX calculation methodology but is no longer being maintained or updated.

**Alternatives**: 
- For production VIX calculations, consider using established financial data providers
- For research purposes, the code can still serve as a reference implementation

**Known Issues**:
- NSE API endpoints may change without notice
- Dependencies are frozen and may have security vulnerabilities
- No active support or bug fixes

## 🎯 Overview

This project calculates **VIX1W** (Weekly VIX) using 7-day option expiries instead of the traditional monthly approach, providing more granular volatility insights for the Indian options market. The implementation follows established VIX calculation methodologies while leveraging modern Python 3.12+ features and comprehensive testing.

**Key Innovation**: By using weekly option expiries, VIX1W provides higher frequency volatility signals that may reveal patterns and divergences useful for quantitative trading strategies.

## 🚀 Features

- **📊 Real-time NSE Data**: Live option chain fetching from NSE India API
- **🧮 Mathematical Accuracy**: Implements official VIX calculation formulas
- **⚡ Modern Python**: Python 3.12+ with type hints, dataclasses, and async support
- **🛡️ Production Ready**: 100% test coverage with comprehensive error handling
- **🔧 Developer Friendly**: Complete development environment with linting, formatting, and type checking

## 📈 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/username/India-VIX1W.git
cd India-VIX1W

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Basic Usage

#### Modern API (Recommended)

```python
from src.data_fetcher import NSEDataFetcher
from src.vix_calculator import VIXCalculator

# Initialize components
fetcher = NSEDataFetcher()
calculator = VIXCalculator(risk_free_rate=0.075)

# Fetch live NSE data
option_chain, underlying_ltp = fetcher.fetch_option_chain()

# Calculate weekly VIX
calculator.load_data(option_chain, underlying_ltp)
vix1w = calculator.calculate_vix1w()

print(f"Weekly VIX (VIX1W): {vix1w}%")
```

#### Legacy Script

```bash
# Run the original monolithic script
python "India VIX1W.py"
```

## 🏗️ Architecture

### Modern Modular Design

```
src/
├── __init__.py
├── data_fetcher.py      # NSE API integration with session management
├── vix_calculator.py    # Core VIX calculation engine
└── models.py           # Data structures (OptionData dataclass)
```

### Key Components

- **`NSEDataFetcher`**: Handles NSE API requests, cookie management, and data parsing
- **`VIXCalculator`**: Implements VIX mathematical formulas with time interpolation
- **`OptionData`**: Type-safe dataclass for option chain data with computed properties

## 🧮 VIX Calculation Methodology

The implementation follows the official methodology:

1. **Data Acquisition**: Fetch NIFTY option chain from NSE API
2. **ATM Determination**: Find At-The-Money strike closest to underlying price
3. **Time Calculation**: Convert expiry dates to time fractions (accounting for 3:30 PM expiry)
4. **Forward Price**: Calculate using put-call parity: `F = Strike + (Call_Price - Put_Price) * e^(r*T)`
5. **Sigma Calculation**: Apply VIX formula with strike price contributions
6. **Interpolation**: Time-weighted interpolation to weekly (7-day) VIX

### Mathematical Formula

```
σ² = (2/T) * Σ[(ΔK/K²) * e^(rT) * Q(K)] - (1/T) * [F/K₀ - 1]²
```

Where:
- `T` = Time to expiry
- `ΔK` = Strike interval (50 points)
- `Q(K)` = Option mid-price (average of bid-ask)
- `F` = Forward index level
- `K₀` = ATM strike price

## 🧪 Testing & Quality

### Comprehensive Test Suite

```bash
# Run all tests with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/unit/        # Unit tests (25 tests)
uv run pytest tests/integration/ # Integration tests (5 tests)
```

### Test Coverage: 100%

- **✅ Mathematical Accuracy**: All VIX formulas validated against known inputs
- **✅ Data Integrity**: NSE API parsing tested with realistic scenarios  
- **✅ Error Handling**: Network failures and malformed data coverage
- **✅ Performance**: Large dataset processing (100+ strikes) validated
- **✅ Edge Cases**: Zero values, boundary conditions, extreme volatility

### Code Quality Tools

```bash
# Linting and formatting
uv run ruff check .     # Fast Python linter
uv run ruff format .    # Code formatting

# Type checking  
uv run mypy .           # Static type analysis

# Testing
uv run pytest          # Run test suite
```

## 📊 Performance

- **Calculation Speed**: <50ms for typical option chain
- **Memory Efficient**: Handles 100+ strikes across multiple expiries
- **Network Resilient**: Automatic retry with exponential backoff
- **Type Safe**: Full mypy compliance with strict mode

## 🛠️ Development

### Development Environment

```bash
# Install development dependencies
uv sync --group dev

# Pre-commit setup (optional)
pre-commit install
```

### Development Tools

- **Package Manager**: `uv` (fast, reliable Python package management)
- **Testing**: `pytest` with coverage, mocking, and async support
- **Linting**: `ruff` (extremely fast Python linter and formatter)
- **Type Checking**: `mypy` with strict configuration
- **Code Quality**: 100% test coverage, comprehensive type hints

### Project Configuration

Modern Python configuration in `pyproject.toml`:

```toml
[project]
requires-python = ">=3.12"
dependencies = ["numpy>=2.3.1", "pandas>=2.3.0", "requests>=2.32.4"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.mypy]
python_version = "3.12"
strict = true
```

## 📈 Research Applications

This implementation enables several quantitative research opportunities:

### 1. **VIX Divergence Analysis**
Compare VIX1W vs standard India VIX to identify:
- Market stress periods with different time horizons
- Term structure of implied volatility
- Potential alpha generation opportunities

### 2. **High-Frequency Volatility Signals**
Weekly recalculation provides:
- More responsive volatility measures
- Earlier detection of volatility regime changes
- Improved risk management for short-term strategies

### 3. **Options Market Microstructure**
Analyze:
- Bid-ask spreads across expiries
- Open interest patterns in weekly vs monthly options
- Liquidity dynamics in different market conditions

## 🗺️ ~~Future Roadmap~~ (Project Archived)

> **Note**: This project is no longer under active development. The following features were planned but will not be implemented.

### ~~Planned Enhancements~~ (Cancelled)

- ~~**📊 Streamlit Dashboard**: Real-time visualization and historical analysis~~
- ~~**🗄️ Database Integration**: Historical VIX1W storage and backtesting~~
- ~~**📡 WebSocket Support**: Live updates with real-time data feeds~~
- ~~**🤖 ML Integration**: Pattern recognition and volatility forecasting~~
- ~~**📈 Backtesting Framework**: Strategy development and validation tools~~

### ~~Research Directions~~ (Not Pursued)

- ~~**Volatility Forecasting**: ML models using VIX1W features~~
- ~~**Cross-Market Analysis**: Compare with other global VIX indices~~
- ~~**Options Strategy Optimization**: Use VIX1W for dynamic hedging~~

## 🤝 Contributing

> **⚠️ This project is archived and no longer accepting contributions.**

This repository is maintained in read-only mode for historical and reference purposes. Pull requests and issues will not be reviewed or merged.

If you find this code useful and want to build upon it:
1. Fork the repository to your own account
2. Create your own maintained version
3. Consider crediting this original work in your project

### For Researchers

The code is available under the MIT license, so you are free to:
- Use it as a reference implementation
- Adapt it for your own research
- Build upon the concepts demonstrated

However, please note that:
- No support will be provided
- Issues will not be addressed
- Pull requests will not be reviewed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NSE India** for providing option chain API access
- **CBOE** for publishing comprehensive VIX calculation methodology
- **Python Community** for excellent quantitative finance tools

## 🔗 References

- [NSE India VIX White Paper](./white_paper_IndiaVIX.pdf)
- [CBOE VIX White Paper](./419_VIX.pdf)
- [VIX Calculation Methodology](https://www.cboe.com/tradable_products/vix/)

---

**⚠️ FINAL NOTE**: This is an archived research project provided for educational and analytical purposes only. The original concept was developed during a holiday project and was modernized with professional-grade code quality, comprehensive testing, and production-ready architecture. However, it is no longer maintained.

**Status**: 🔴 **ARCHIVED - NO LONGER MAINTAINED**

*This project served its purpose and is now preserved for historical reference.*