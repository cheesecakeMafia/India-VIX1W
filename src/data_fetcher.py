"""Data fetching module for NSE option chain data."""

from typing import Any

import pandas as pd
import requests


class NSEDataFetcher:
    """Fetches option chain data from NSE India website."""

    URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    HEADERS = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
    }

    def __init__(self) -> None:
        self.session = requests.Session()

    def fetch_option_chain(self) -> dict[str, Any]:
        """Fetch option chain data from NSE API."""
        request = self.session.get(self.URL, headers=self.HEADERS)
        cookies = dict(request.cookies)
        response = self.session.get(self.URL, headers=self.HEADERS, cookies=cookies)
        return response.json()

    def parse_option_data(self, response: dict[str, Any]) -> tuple[pd.DataFrame, float]:
        """Parse raw NSE response into structured DataFrame."""
        df = pd.DataFrame(response["records"]["data"]).fillna(0)

        data = []
        for i in range(len(df)):
            call_oi = call_coi = put_oi = put_coi = 0
            call_IV = put_IV = call_ltp = put_ltp = call_bid = call_ask = put_bid = put_ask = float(
                0
            )
            strike = df.iloc[i, 0]
            expiry = df.iloc[i, 1]

            if df.iloc[i, -1] != 0:
                call_oi = df.iloc[i, -1]["openInterest"]
                call_coi = df.iloc[i, -1]["changeinOpenInterest"]
                call_ltp = df.iloc[i, -1]["lastPrice"]
                call_bid = df.iloc[i, -1]["bidprice"]
                call_ask = df.iloc[i, -1]["askPrice"]
                call_IV = df.iloc[i, -1]["impliedVolatility"]

            if df.iloc[i, -2] != 0:
                put_oi = df.iloc[i, -2]["openInterest"]
                put_coi = df.iloc[i, -2]["changeinOpenInterest"]
                put_ltp = df.iloc[i, -2]["lastPrice"]
                put_bid = df.iloc[i, -2]["bidprice"]
                put_ask = df.iloc[i, -2]["askPrice"]
                put_IV = df.iloc[i, -2]["impliedVolatility"]

            option_data = {
                "Expiry": expiry,
                "Call OI": call_oi,
                "Call C_OI": call_coi,
                "Call IV": call_IV,
                "Call Bid": call_bid,
                "Call Ask": call_ask,
                "Call LTP": call_ltp,
                "Strike": strike,
                "Put Bid": put_bid,
                "Put Ask": put_ask,
                "Put LTP": put_ltp,
                "Put IV": put_IV,
                "Put C_OI": put_coi,
                "Put OI": put_oi,
            }
            data.append(option_data)

        optionchain = pd.DataFrame(data)
        underlying_ltp = df.iloc[0, -2]["underlyingValue"]

        return optionchain, underlying_ltp
