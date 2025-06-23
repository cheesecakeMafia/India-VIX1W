''' I have used the NSE India VIX white paper and the CBOE VIX white paper to understand the methodology and generate the VIX on weekly expiries in this project.

This is just a research project and may have some bugs in it. I would really appreciate if you find it useful and make the code cleaner and more efficient.
Would love to interact and get your feedback on what I could have done better.

By - cheesecakeMafia '''


# Import required libraries
import requests
import pandas as pd
import numpy as np
import math
from datetime import datetime
from datetime import timedelta

# URL to get NIFTY option chain 
url = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'

# Create a session and scrape the data from the NSE website
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
    ,'accept-encoding': 'gzip, deflate, br'
    ,'accept-language': 'en-US,en;q=0.9'    
}


# Create a session and send request to get the data from the website
session = requests.Session()
request = session.get(url, headers=headers)
cookies = dict(request.cookies)
response = session.get(url, headers=headers, cookies=cookies).json()
rawdata = pd.DataFrame(response)

# Take the required cell into a dataframe to work on it
df= pd.DataFrame(response["records"]['data']).fillna(0)

# Convert the dataframe from a dict structure into a data frame structure
def option_dataframe(df):
    data = []
    for i in range(len(df)):
        call_oi = call_coi = put_oi = put_coi = int(0)
        call_IV = put_IV = call_ltp = put_ltp = call_bid = call_ask = put_bid = put_ask = float(0)
        strike = df.iloc[i,0]
        expiry = df.iloc[i,1]
        if(df.iloc[i,-1] == 0):
            call_coi = 0
        else:
            call_oi = df.iloc[i,-1]["openInterest"]
            call_coi = df.iloc[i,-1]["changeinOpenInterest"]
            call_ltp = df.iloc[i,-1]['lastPrice']
            call_bid = df.iloc[i,-1]["bidprice"]
            call_ask = df.iloc[i,-1]["askPrice"]
            call_IV = df.iloc[i,-1]['impliedVolatility']
        
        if(df.iloc[i,-2] == 0):
            put_coi = 0
        else:
            put_oi = df.iloc[i,-2]["openInterest"]
            put_coi = df.iloc[i,-2]["changeinOpenInterest"]
            put_ltp = df.iloc[i,-2]['lastPrice']
            put_bid = df.iloc[i,-2]["bidprice"]
            put_ask = df.iloc[i,-2]["askPrice"]
            put_IV = df.iloc[i,-2]['impliedVolatility']
            
        option_data = {"Expiry": expiry,
            "Call OI" : call_oi, "Call C_OI" : call_coi,"Call IV": call_IV , "Call Bid" : call_bid, "Call Ask" : call_ask , "Call LTP" : call_ltp, "Strike" : strike,
              "Put Bid" : put_bid, "Put Ask" : put_ask , "Put LTP" : put_ltp ,"Put IV" : put_IV , "Put C_OI" : put_coi, "Put OI" : put_oi
        }
        data.append(option_data)
    optionchain = pd.DataFrame(data)

    return optionchain , df.iloc[0,-2]["underlyingValue"]

# Create an instance of the function by calling it
optionchain  , underlying_ltp = option_dataframe(df) 

# Create a list of strike prices and expires sorted in ascending order
strike_list = pd.Series(optionchain["Strike"].unique()).sort_values(ascending=True)
expiries_list = pd.to_datetime(optionchain["Expiry"].unique()).sort_values(ascending=True)


# Create a dictionary contaitng all the data sorted by the expiry
def by_expiry(optionchain, cutoff = 50):
    optionchain.sort_values(by=["Expiry", "Strike"], ascending=True, inplace=True)
    option_dict = {}
    optionchain["Expiry"] = pd.to_datetime(optionchain["Expiry"])
    for i in  range(len(expiries_list)):
        option_dict[i] = optionchain.loc[optionchain["Expiry"] == expiries_list[i]]
        option_dict[i] = option_dict[i].drop(option_dict[i][(option_dict[i]["Call OI"]<=cutoff) | (option_dict[i]["Put OI"]<=cutoff)].index)
        option_dict[i] = option_dict[i].drop(option_dict[i][(option_dict[i]["Call LTP"]==0) | (option_dict[i]["Put LTP"]==0)].index)
        option_dict[i].reset_index(inplace=True,drop=True)
        option_dict[i].drop(["Expiry"], axis=1, inplace=True)
#         option_dict[i].drop(["Call LTP"])
    return option_dict


# Create another dictionary contaitng all the data sorted by the strikes
def by_strike(optionchain, cutoff = 50):
    optionchain.sort_values(by=["Strike","Expiry"], inplace=True, ascending=True)
    option_dict = {}
    for i in  strike_list:
        option_dict[i] = optionchain.loc[optionchain["Strike"] == i]
        option_dict[i] = option_dict[i].drop(option_dict[i][(option_dict[i]["Call OI"]<=cutoff) | (option_dict[i]["Put OI"]<=cutoff)].index)
        option_dict[i] = option_dict[i].drop(option_dict[i][(option_dict[i]["Call LTP"] == 0) | (option_dict[i]["Put LTP"] == 0)].index)
        option_dict[i].reset_index(inplace=True,drop=True)
        option_dict[i].drop(["Strike"], axis=1, inplace=True)
    return option_dict


# A function to get the ATM strike. The logic being the strike nearest to the index value.
def strike_ATM():
    m = []
    a = 0
    for i in range(len(strike_list)):
        a = abs(underlying_ltp - strike_list[i])
        m.append(a)
        if a == min(m):
            min_strike = strike_list[i]
    return min_strike

ATM = strike_ATM()

# Risk free interest rate is taken as 7.5% which is 100 bps above the repo rate
r = 0.075

# Getting the nearest expiry date and one after that since we are using weekly expiries. The timedelta is added cause option don't expire on 12AM on the given date\
# but at 3:30 PM on the same day and hence the difference of 15.5 hours
nearest_expiry_date = expiries_list[0] + timedelta(hours = 15.5)
next_expiry_date =  expiries_list[1] + timedelta(hours = 15.5)


# Function to calculate the time to expiry in minutes
def calculate_time_to_expiry(expiry = nearest_expiry_date):
    return ((expiry - datetime.now()).days*1440 + (expiry - datetime.now()).seconds//60)/ 525_600

# Time to expiry is calculated in minutes based on the formula T = {M_current_day + M_settlement_day + M_other_days}/ Minutes in a year
T_1 = calculate_time_to_expiry(nearest_expiry_date)
T_2 = calculate_time_to_expiry(next_expiry_date)

# Here I am using the above defined function to get a dictionary of all the dataframe with the same expiry. Cutoff 20 represents OI has to be greater than 20.  
expiry_df = by_expiry(optionchain, cutoff = 20)
strike_df = by_strike(optionchain, cutoff = 20)


# USing the above dict to get the nearest expiry and the one after that 
near_expiry = expiry_df[0]
far_expiry = expiry_df[1]


# Dropping columns with no use
near_expiry.drop(columns=["Call OI","Call C_OI","Call IV","Put IV","Put C_OI", "Put OI"], inplace=True)
far_expiry.drop(columns=["Call OI","Call C_OI","Call IV","Put IV","Put C_OI", "Put OI"], inplace=True)

# Difference between consequitive strikes
del_k = 50


# A function to do the calculation on the OTM strikes of call and put of the option dataframe which inturn returns a modified dataframe
def cal_Variables(df, time = T_1):
    for i, strike in enumerate(df["Strike"]):
        df.loc[i,"F"] = strike + (df.loc[i,"Call LTP"] - df.loc[i,"Put LTP"])*math.exp(r*time)
        df.loc[i,"Call Spread"] = (df.loc[i, "Call Ask"] - df.loc[i, "Call Bid"]) * 200 / (df.loc[i, "Call Ask"] + df.loc[i,"Call Bid"])
        df.loc[i,"Put Spread"] = (df.loc[i, "Put Ask"] - df.loc[i, "Put Bid"]) * 200 / (df.loc[i, "Put Ask"] + df.loc[i,"Put Bid"])
        if strike < ATM :
            df.loc[i,"A"] = ((del_k * math.exp(r*time) * (df.loc[i,"Put Bid"] + df.loc[i,"Put Ask"]))) / (2 * strike**2)
        elif strike > ATM:
            df.loc[i,"A"] = ((del_k * math.exp(r*time) * (df.loc[i,"Call Bid"] + df.loc[i,"Call Ask"]))) / (2 * strike**2)
        else :
            df.loc[i,"A"] = ((del_k * math.exp(r*time) * (df.loc[i,"Call Bid"] + df.loc[i,"Call Ask"]))) / (4 * strike**2)  +  ((del_k * math.exp(r*time) * (df.loc[i,"Put Bid"] + df.loc[i,"Put Ask"])) / (4 * strike**2))

    return df

# Calling the function twice to generate a modified near and far expiry dataframe
near_expiry = cal_Variables(near_expiry, time=T_1)
far_expiry = cal_Variables(far_expiry, time=T_2)


# Calculating the F term from the dataframe by taking the average of F over all strikes
F_near = sum(near_expiry["F"])/len(near_expiry.index)
F_far = sum(far_expiry["F"])/len(far_expiry.index)


# Calculating the second term of the sigma formula. Named B for easier nomenclature.
B_1 = ((F_near/ATM) - 1)**2 / T_1
B_2 = ((F_far/ATM) - 1)**2 / T_2


# Using the sigma formula to get the sigmas of near and far expiries
sigma_1 = np.sqrt((near_expiry["A"].sum())*2/T_1 - B_1)
sigma_2 = np.sqrt((far_expiry["A"].sum())*2/T_2 - B_2)

# Now interpolating the two and multiplying by 100 to get the value of the weekly VIX i.e. VIX1W We interpolate using the formula used in the white paper
NT_7 = 24*7*60
NT_1 = T_1 * 525_600
NT_2 = T_2 * 525_600
X = ((NT_2 - NT_7)/(NT_2 - NT_1))
Y = ((NT_7 - NT_1)/(NT_2 - NT_1))

sigma = math.sqrt( (X*T_1*sigma_1*sigma_1) + (Y*T_2*sigma_2*sigma_2) * 365/7)

VIX1W = np.round(100 * sigma,2)

print(f'The VIX value for weekly expiries we get is {VIX1W}, rounded to two decimal places.')

""" The value we get is around 9.75 while the India VIX monthly is around 10.95 """