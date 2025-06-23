# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a quantitative finance research project that calculates India VIX (volatility index) using weekly options instead of the standard monthly options methodology. The implementation follows the NSE India VIX and CBOE VIX white papers to compute a weekly volatility index (VIX1W).

## Core Architecture

The main script `India VIX1W.py` implements a single-file volatility calculation pipeline:

1. **Data Acquisition**: Scrapes NSE NIFTY option chain data via their public API using requests with proper headers and session management
2. **Data Processing**: Converts nested JSON response into structured pandas DataFrames with option chain data (strikes, expiries, implied volatility, open interest)
3. **VIX Calculation**: Implements the mathematical formula from VIX white papers including:
   - Forward price calculation using put-call parity
   - Time-to-expiry calculations in minutes
   - ATM (At-The-Money) strike determination
   - Sigma calculation for near-term and next-term options
   - Final interpolation to weekly VIX value

## Key Functions

- `option_dataframe()`: Converts raw NSE API response to structured DataFrame
- `by_expiry()` & `by_strike()`: Creates dictionaries organizing data by expiry dates and strike prices  
- `strike_ATM()`: Finds the ATM strike closest to underlying price
- `calculate_time_to_expiry()`: Converts expiry dates to time fractions
- `cal_Variables()`: Core VIX calculation applying the mathematical formulas

## Development Commands

This is a standalone Python script with no build system. To run:

```bash
python "India VIX1W.py"
```

Dependencies are imported at the top and include: requests, pandas, numpy, math, datetime

## Data Sources

- Uses NSE India's public option chain API: `https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY`
- Requires proper headers to mimic browser requests for successful data retrieval
- Risk-free rate hardcoded to 7.5% (100 bps above repo rate)

## Key Constants

- `del_k = 50`: Strike price intervals
- `r = 0.075`: Risk-free interest rate  
- `cutoff = 20`: Minimum open interest threshold for option filtering
- Expiry time adjustment: +15.5 hours (options expire 3:30 PM, not midnight)

## Current Limitations

The author notes this is research code that may contain bugs and requests help with code optimization and cleaning. Future plans include database integration and Streamlit dashboard development.