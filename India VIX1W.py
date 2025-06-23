"""India VIX1W Calculator - Weekly Volatility Index for NIFTY Options

Implements VIX calculation methodology from NSE India VIX and CBOE VIX white papers
to compute weekly volatility index using 7-day expiry options instead of monthly.

Author: cheesecakeMafia
Note: Research project - contributions welcome for optimization and bug fixes
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import requests


@dataclass
class OptionData:
    """Structured representation of option chain data for a single strike."""

    expiry: str
    strike: float
    call_oi: int = 0
    call_coi: int = 0
    call_iv: float = 0.0
    call_bid: float = 0.0
    call_ask: float = 0.0
    call_ltp: float = 0.0
    put_oi: int = 0
    put_coi: int = 0
    put_iv: float = 0.0
    put_bid: float = 0.0
    put_ask: float = 0.0
    put_ltp: float = 0.0

    @property
    def call_mid_price(self) -> float:
        """Calculate call option mid price from bid-ask."""
        return (self.call_bid + self.call_ask) / 2

    @property
    def put_mid_price(self) -> float:
        """Calculate put option mid price from bid-ask."""
        return (self.put_bid + self.put_ask) / 2

    @property
    def call_spread_pct(self) -> float:
        """Calculate call option bid-ask spread as percentage."""
        if self.call_bid + self.call_ask == 0:
            return 0.0
        return (self.call_ask - self.call_bid) * 200 / (self.call_ask + self.call_bid)

    @property
    def put_spread_pct(self) -> float:
        """Calculate put option bid-ask spread as percentage."""
        if self.put_bid + self.put_ask == 0:
            return 0.0
        return (self.put_ask - self.put_bid) * 200 / (self.put_ask + self.put_bid)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for DataFrame compatibility."""
        return {
            "Expiry": self.expiry,
            "Strike": self.strike,
            "Call OI": self.call_oi,
            "Call C_OI": self.call_coi,
            "Call IV": self.call_iv,
            "Call Bid": self.call_bid,
            "Call Ask": self.call_ask,
            "Call LTP": self.call_ltp,
            "Put OI": self.put_oi,
            "Put C_OI": self.put_coi,
            "Put IV": self.put_iv,
            "Put Bid": self.put_bid,
            "Put Ask": self.put_ask,
            "Put LTP": self.put_ltp,
        }


class VIXCalculator:
    """Weekly VIX calculator using NSE NIFTY options data."""

    def __init__(self, risk_free_rate: float = 0.075, strike_interval: int = 50):
        """Initialize VIX calculator with market parameters.

        Args:
            risk_free_rate: Risk-free interest rate (default 7.5%)
            strike_interval: Strike price interval (default 50)
        """
        self.risk_free_rate = risk_free_rate
        self.strike_interval = strike_interval
        self._option_chain: pd.DataFrame | None = None
        self._underlying_ltp: float | None = None

    @property
    def option_chain(self) -> pd.DataFrame:
        """Get processed option chain data."""
        if self._option_chain is None:
            raise ValueError("Option chain data not loaded. Call fetch_data() first.")
        return self._option_chain

    @property
    def underlying_ltp(self) -> float:
        """Get underlying index LTP."""
        if self._underlying_ltp is None:
            raise ValueError("Underlying LTP not available. Call fetch_data() first.")
        return self._underlying_ltp

    @property
    def atm_strike(self) -> float:
        """Find At-The-Money strike closest to underlying value."""
        strikes = self.option_chain["Strike"].unique()
        differences = [abs(self.underlying_ltp - strike) for strike in strikes]
        min_idx = differences.index(min(differences))
        return strikes[min_idx]

    def fetch_data(self) -> None:
        """Fetch and process NSE option chain data."""
        session = requests.Session()
        request = session.get(URL, headers=HEADERS)
        cookies = dict(request.cookies)
        response = session.get(URL, headers=HEADERS, cookies=cookies).json()

        df = pd.DataFrame(response["records"]["data"]).fillna(0)
        self._option_chain, self._underlying_ltp = option_dataframe(df)

    def calculate_vix1w(self, oi_cutoff: int = 20) -> float:
        """Calculate weekly VIX using processed option data.

        Args:
            oi_cutoff: Minimum open interest threshold

        Returns:
            Weekly VIX value as percentage
        """
        # Group data and calculate VIX using existing logic
        expiry_df = by_expiry(self.option_chain, cutoff=oi_cutoff)

        # Get first two expiries
        near_expiry = expiry_df[0].copy()
        far_expiry = expiry_df[1].copy()

        # Remove unused columns
        cols_to_drop = ["Call OI", "Call C_OI", "Call IV", "Put IV", "Put C_OI", "Put OI"]
        near_expiry.drop(columns=cols_to_drop, inplace=True)
        far_expiry.drop(columns=cols_to_drop, inplace=True)

        # Calculate expiry times
        expiries_list = pd.to_datetime(self.option_chain["Expiry"].unique()).sort_values(
            ascending=True
        )
        nearest_expiry_date = expiries_list[0] + timedelta(hours=15.5)
        next_expiry_date = expiries_list[1] + timedelta(hours=15.5)

        T_1 = self._calculate_time_to_expiry(nearest_expiry_date)
        T_2 = self._calculate_time_to_expiry(next_expiry_date)

        # Calculate VIX variables
        near_expiry = cal_Variables(near_expiry, time=T_1)
        far_expiry = cal_Variables(far_expiry, time=T_2)

        # Final VIX calculation
        F_near = near_expiry["F"].mean()
        F_far = far_expiry["F"].mean()

        atm = self.atm_strike
        B_1 = ((F_near / atm) - 1) ** 2 / T_1
        B_2 = ((F_far / atm) - 1) ** 2 / T_2

        sigma_1 = np.sqrt((near_expiry["A"].sum()) * 2 / T_1 - B_1)
        sigma_2 = np.sqrt((far_expiry["A"].sum()) * 2 / T_2 - B_2)

        # Interpolate to weekly VIX
        NT_7 = 24 * 7 * 60  # Minutes in 7 days
        NT_1 = T_1 * 525_600
        NT_2 = T_2 * 525_600
        X = (NT_2 - NT_7) / (NT_2 - NT_1)
        Y = (NT_7 - NT_1) / (NT_2 - NT_1)

        sigma = math.sqrt((X * T_1 * sigma_1 * sigma_1) + (Y * T_2 * sigma_2 * sigma_2) * 365 / 7)

        return round(100 * sigma, 2)

    def _calculate_time_to_expiry(self, expiry: datetime) -> float:
        """Calculate time to expiry as fraction of year."""
        return (
            (expiry - datetime.now()).days * 1440 + (expiry - datetime.now()).seconds // 60
        ) / 525_600


# NSE NIFTY option chain API endpoint
URL: str = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

# HTTP headers to mimic browser request for NSE API
HEADERS: dict[str, str] = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
}


# Fetch option chain data from NSE API
session: requests.Session = requests.Session()
request: requests.Response = session.get(URL, headers=HEADERS)
cookies: dict[str, str] = dict(request.cookies)
response: dict[str, Any] = session.get(URL, headers=HEADERS, cookies=cookies).json()
rawdata: pd.DataFrame = pd.DataFrame(response)

# Extract option chain records and fill missing values
df: pd.DataFrame = pd.DataFrame(response["records"]["data"]).fillna(0)


def option_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Convert NSE option chain response into structured DataFrame.

    Args:
        df: Raw option chain data from NSE API

    Returns:
        Tuple of (processed option chain DataFrame, underlying LTP)
    """
    data: list[OptionData] = []

    for i in range(len(df)):
        strike: float = df.iloc[i, 0]
        expiry: str = df.iloc[i, 1]

        # Extract call option data
        call_data = df.iloc[i, -1]
        if call_data == 0:
            call_oi = call_coi = 0
            call_iv = call_ltp = call_bid = call_ask = 0.0
        else:
            call_oi = call_data["openInterest"]
            call_coi = call_data["changeinOpenInterest"]
            call_ltp = call_data["lastPrice"]
            call_bid = call_data["bidprice"]
            call_ask = call_data["askPrice"]
            call_iv = call_data["impliedVolatility"]

        # Extract put option data
        put_data = df.iloc[i, -2]
        if put_data == 0:
            put_oi = put_coi = 0
            put_iv = put_ltp = put_bid = put_ask = 0.0
        else:
            put_oi = put_data["openInterest"]
            put_coi = put_data["changeinOpenInterest"]
            put_ltp = put_data["lastPrice"]
            put_bid = put_data["bidprice"]
            put_ask = put_data["askPrice"]
            put_iv = put_data["impliedVolatility"]

        # Create structured option data
        option = OptionData(
            expiry=expiry,
            strike=strike,
            call_oi=call_oi,
            call_coi=call_coi,
            call_iv=call_iv,
            call_bid=call_bid,
            call_ask=call_ask,
            call_ltp=call_ltp,
            put_oi=put_oi,
            put_coi=put_coi,
            put_iv=put_iv,
            put_bid=put_bid,
            put_ask=put_ask,
            put_ltp=put_ltp,
        )
        data.append(option)

    # Convert to DataFrame for compatibility with existing code
    optionchain = pd.DataFrame([opt.to_dict() for opt in data])
    underlying_value: float = df.iloc[0, -2]["underlyingValue"]

    return optionchain, underlying_value


# Process raw option data into structured format
optionchain: pd.DataFrame
underlying_ltp: float
optionchain, underlying_ltp = option_dataframe(df)

# Extract and sort unique strikes and expiry dates
strike_list: pd.Series = pd.Series(optionchain["Strike"].unique()).sort_values(ascending=True)
expiries_list: pd.Series = pd.to_datetime(optionchain["Expiry"].unique()).sort_values(
    ascending=True
)


def by_expiry(optionchain: pd.DataFrame, cutoff: int = 50) -> dict[int, pd.DataFrame]:
    """Group option chain data by expiry date with OI filtering.

    Args:
        optionchain: Option chain DataFrame
        cutoff: Minimum open interest threshold

    Returns:
        Dictionary mapping expiry index to filtered DataFrame
    """
    optionchain.sort_values(by=["Expiry", "Strike"], ascending=True, inplace=True)
    option_dict = {}
    optionchain["Expiry"] = pd.to_datetime(optionchain["Expiry"])
    for i in range(len(expiries_list)):
        option_dict[i] = optionchain.loc[optionchain["Expiry"] == expiries_list[i]]
        option_dict[i] = option_dict[i].drop(
            option_dict[i][
                (option_dict[i]["Call OI"] <= cutoff) | (option_dict[i]["Put OI"] <= cutoff)
            ].index
        )
        option_dict[i] = option_dict[i].drop(
            option_dict[i][
                (option_dict[i]["Call LTP"] == 0) | (option_dict[i]["Put LTP"] == 0)
            ].index
        )
        option_dict[i].reset_index(inplace=True, drop=True)
        option_dict[i].drop(["Expiry"], axis=1, inplace=True)
    #         option_dict[i].drop(["Call LTP"])
    return option_dict


def by_strike(optionchain: pd.DataFrame, cutoff: int = 50) -> dict[float, pd.DataFrame]:
    """Group option chain data by strike price with OI filtering.

    Args:
        optionchain: Option chain DataFrame
        cutoff: Minimum open interest threshold

    Returns:
        Dictionary mapping strike price to filtered DataFrame
    """
    optionchain.sort_values(by=["Strike", "Expiry"], inplace=True, ascending=True)
    option_dict = {}
    for i in strike_list:
        option_dict[i] = optionchain.loc[optionchain["Strike"] == i]
        option_dict[i] = option_dict[i].drop(
            option_dict[i][
                (option_dict[i]["Call OI"] <= cutoff) | (option_dict[i]["Put OI"] <= cutoff)
            ].index
        )
        option_dict[i] = option_dict[i].drop(
            option_dict[i][
                (option_dict[i]["Call LTP"] == 0) | (option_dict[i]["Put LTP"] == 0)
            ].index
        )
        option_dict[i].reset_index(inplace=True, drop=True)
        option_dict[i].drop(["Strike"], axis=1, inplace=True)
    return option_dict


def strike_ATM() -> float:
    """Find At-The-Money strike price closest to underlying value.

    Returns:
        Strike price closest to current underlying LTP
    """
    differences = [abs(underlying_ltp - strike) for strike in strike_list]
    min_idx = differences.index(min(differences))
    return strike_list[min_idx]


ATM: float = strike_ATM()

# Risk-free interest rate: 7.5% (100 bps above repo rate)
r: float = 0.075

# Adjust expiry times: options expire at 3:30 PM, not midnight (15.5 hour offset)
nearest_expiry_date: datetime = expiries_list[0] + timedelta(hours=15.5)
next_expiry_date: datetime = expiries_list[1] + timedelta(hours=15.5)


def calculate_time_to_expiry(expiry: datetime) -> float:
    """Calculate time to expiry as fraction of year.

    Args:
        expiry: Option expiry datetime

    Returns:
        Time to expiry as fraction of year (T in VIX formula)
    """
    return (
        (expiry - datetime.now()).days * 1440 + (expiry - datetime.now()).seconds // 60
    ) / 525_600


# Calculate time to expiry as fraction of year (T in VIX formula)
T_1: float = calculate_time_to_expiry(nearest_expiry_date)
T_2: float = calculate_time_to_expiry(next_expiry_date)

# Group data by expiry and strike with minimum OI threshold of 20
expiry_df: dict[int, pd.DataFrame] = by_expiry(optionchain, cutoff=20)
strike_df: dict[float, pd.DataFrame] = by_strike(optionchain, cutoff=20)


# Extract near-term and next-term expiry data
near_expiry: pd.DataFrame = expiry_df[0]
far_expiry: pd.DataFrame = expiry_df[1]


# Remove unused columns for VIX calculation
near_expiry.drop(
    columns=["Call OI", "Call C_OI", "Call IV", "Put IV", "Put C_OI", "Put OI"], inplace=True
)
far_expiry.drop(
    columns=["Call OI", "Call C_OI", "Call IV", "Put IV", "Put C_OI", "Put OI"], inplace=True
)

# Strike price interval (Δk in VIX formula)
del_k: int = 50


def cal_Variables(df: pd.DataFrame, time: float) -> pd.DataFrame:
    """Calculate VIX formula variables for each strike.

    Computes forward price (F), bid-ask spreads, and contribution (A)
    for each strike using VIX methodology.

    Args:
        df: Option data DataFrame for specific expiry
        time: Time to expiry as fraction of year

    Returns:
        DataFrame with calculated VIX variables
    """
    for i, strike in enumerate(df["Strike"]):
        df.loc[i, "F"] = strike + (df.loc[i, "Call LTP"] - df.loc[i, "Put LTP"]) * math.exp(
            r * time
        )
        df.loc[i, "Call Spread"] = (
            (df.loc[i, "Call Ask"] - df.loc[i, "Call Bid"])
            * 200
            / (df.loc[i, "Call Ask"] + df.loc[i, "Call Bid"])
        )
        df.loc[i, "Put Spread"] = (
            (df.loc[i, "Put Ask"] - df.loc[i, "Put Bid"])
            * 200
            / (df.loc[i, "Put Ask"] + df.loc[i, "Put Bid"])
        )
        if strike < ATM:
            df.loc[i, "A"] = (
                del_k * math.exp(r * time) * (df.loc[i, "Put Bid"] + df.loc[i, "Put Ask"])
            ) / (2 * strike**2)
        elif strike > ATM:
            df.loc[i, "A"] = (
                del_k * math.exp(r * time) * (df.loc[i, "Call Bid"] + df.loc[i, "Call Ask"])
            ) / (2 * strike**2)
        else:
            df.loc[i, "A"] = (
                del_k * math.exp(r * time) * (df.loc[i, "Call Bid"] + df.loc[i, "Call Ask"])
            ) / (4 * strike**2) + (
                (del_k * math.exp(r * time) * (df.loc[i, "Put Bid"] + df.loc[i, "Put Ask"]))
                / (4 * strike**2)
            )

    return df


# Calculate VIX variables for both expiry periods
near_expiry = cal_Variables(near_expiry, time=T_1)
far_expiry = cal_Variables(far_expiry, time=T_2)


# Calculate forward index levels (F) for both expiries
F_near: float = sum(near_expiry["F"]) / len(near_expiry.index)
F_far: float = sum(far_expiry["F"]) / len(far_expiry.index)


# Calculate second term of sigma formula (B term)
B_1: float = ((F_near / ATM) - 1) ** 2 / T_1
B_2: float = ((F_far / ATM) - 1) ** 2 / T_2


# Calculate sigma (volatility) for both expiries using VIX formula
sigma_1: float = np.sqrt((near_expiry["A"].sum()) * 2 / T_1 - B_1)
sigma_2: float = np.sqrt((far_expiry["A"].sum()) * 2 / T_2 - B_2)

# Interpolate to get weekly VIX (VIX1W) using time-weighted average
NT_7: int = 24 * 7 * 60  # Minutes in 7 days
NT_1: float = T_1 * 525_600  # Minutes to near expiry
NT_2: float = T_2 * 525_600  # Minutes to far expiry
X: float = (NT_2 - NT_7) / (NT_2 - NT_1)  # Weight for near term
Y: float = (NT_7 - NT_1) / (NT_2 - NT_1)  # Weight for far term

# Final interpolated sigma calculation
sigma: float = math.sqrt((X * T_1 * sigma_1 * sigma_1) + (Y * T_2 * sigma_2 * sigma_2) * 365 / 7)

# Convert to percentage and round to 2 decimal places
VIX1W: float = np.round(100 * sigma, 2)

print(f"Weekly VIX (VIX1W) value: {VIX1W}%")

""" The value we get is around 9.75 while the India VIX monthly is around 10.95 """
