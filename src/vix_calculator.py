"""VIX calculation module implementing CBOE/NSE methodology."""

import math
import pandas as pd
from datetime import datetime
from typing import Dict


class VIXCalculator:
    """Calculates VIX using weekly options data."""
    
    def __init__(self, risk_free_rate: float = 0.075, delta_k: int = 50) -> None:
        self.risk_free_rate = risk_free_rate
        self.delta_k = delta_k
    
    def get_atm_strike(self, strike_list: pd.Series, underlying_price: float) -> float:
        """Find ATM strike closest to underlying price."""
        differences = [abs(underlying_price - strike) for strike in strike_list]
        min_index = differences.index(min(differences))
        return strike_list.iloc[min_index]
    
    def calculate_time_to_expiry(self, expiry_date: datetime) -> float:
        """Calculate time to expiry in years (minutes/525600)."""
        time_diff = expiry_date - datetime.now()
        minutes = time_diff.days * 1440 + time_diff.seconds // 60
        return minutes / 525_600
    
    def organize_by_expiry(self, optionchain: pd.DataFrame, cutoff: int = 50) -> Dict[int, pd.DataFrame]:
        """Organize option data by expiry dates."""
        optionchain = optionchain.copy()
        optionchain.sort_values(by=["Expiry", "Strike"], ascending=True, inplace=True)
        
        expiries_list = pd.to_datetime(optionchain["Expiry"].unique()).sort_values(ascending=True)
        option_dict = {}
        optionchain["Expiry"] = pd.to_datetime(optionchain["Expiry"])
        
        for i in range(len(expiries_list)):
            option_dict[i] = optionchain.loc[optionchain["Expiry"] == expiries_list[i]].copy()
            # Filter out low OI and zero LTP options
            mask = (
                (option_dict[i]["Call OI"] > cutoff) & 
                (option_dict[i]["Put OI"] > cutoff) &
                (option_dict[i]["Call LTP"] > 0) & 
                (option_dict[i]["Put LTP"] > 0)
            )
            option_dict[i] = option_dict[i][mask].reset_index(drop=True)
            option_dict[i].drop(["Expiry"], axis=1, inplace=True)
            
        return option_dict
    
    def calculate_vix_variables(self, df: pd.DataFrame, time_to_expiry: float, atm_strike: float) -> pd.DataFrame:
        """Calculate VIX formula variables for each strike."""
        df = df.copy()
        
        for i, strike in enumerate(df["Strike"]):
            # Forward price calculation
            df.loc[i, "F"] = strike + (df.loc[i, "Call LTP"] - df.loc[i, "Put LTP"]) * math.exp(self.risk_free_rate * time_to_expiry)
            
            # Bid-ask spreads
            df.loc[i, "Call Spread"] = (df.loc[i, "Call Ask"] - df.loc[i, "Call Bid"]) * 200 / (df.loc[i, "Call Ask"] + df.loc[i, "Call Bid"])
            df.loc[i, "Put Spread"] = (df.loc[i, "Put Ask"] - df.loc[i, "Put Bid"]) * 200 / (df.loc[i, "Put Ask"] + df.loc[i, "Put Bid"])
            
            # VIX contribution calculation
            if strike < atm_strike:
                df.loc[i, "A"] = ((self.delta_k * math.exp(self.risk_free_rate * time_to_expiry) * 
                                 (df.loc[i, "Put Bid"] + df.loc[i, "Put Ask"])) / (2 * strike**2))
            elif strike > atm_strike:
                df.loc[i, "A"] = ((self.delta_k * math.exp(self.risk_free_rate * time_to_expiry) * 
                                 (df.loc[i, "Call Bid"] + df.loc[i, "Call Ask"])) / (2 * strike**2))
            else:  # ATM strike
                df.loc[i, "A"] = ((self.delta_k * math.exp(self.risk_free_rate * time_to_expiry) * 
                                 (df.loc[i, "Call Bid"] + df.loc[i, "Call Ask"])) / (4 * strike**2) +
                                (self.delta_k * math.exp(self.risk_free_rate * time_to_expiry) * 
                                 (df.loc[i, "Put Bid"] + df.loc[i, "Put Ask"])) / (4 * strike**2))
        
        return df
    
    def calculate_sigma(self, df: pd.DataFrame, time_to_expiry: float, forward_price: float, atm_strike: float) -> float:
        """Calculate sigma using VIX formula."""
        # Second term of sigma formula
        B = ((forward_price / atm_strike) - 1)**2 / time_to_expiry
        
        # Calculate sigma
        sigma_squared = (df["A"].sum() * 2 / time_to_expiry) - B
        return math.sqrt(sigma_squared)
    
    def interpolate_vix(self, sigma_1: float, sigma_2: float, T_1: float, T_2: float) -> float:
        """Interpolate VIX from near-term and next-term sigmas."""
        NT_7 = 24 * 7 * 60  # 7 days in minutes
        NT_1 = T_1 * 525_600  # Convert to minutes
        NT_2 = T_2 * 525_600  # Convert to minutes
        
        X = (NT_2 - NT_7) / (NT_2 - NT_1)
        Y = (NT_7 - NT_1) / (NT_2 - NT_1)
        
        sigma = math.sqrt(((X * T_1 * sigma_1**2) + (Y * T_2 * sigma_2**2)) * 365/7)
        
        return 100 * sigma