import numpy as np
import scipy.stats as si
import pandas as pd

# ==============================================================================
# 1. BLACK-SCHOLES FORMULAS FOR OPTION GREEKS
# ==============================================================================

def bsm_greeks(S, K, T, r, sigma, option_type="call"):
    """
    Calculate Black-Scholes-Merton option price and Greeks (Delta, Gamma, Theta, Vega, Rho)
    
    Parameters:
    S : float : Current stock price
    K : float : Strike price
    T : float : Time to expiration in years (e.g. 10 days = 10/365)
    r : float : Risk-free interest rate (e.g. 0.07 for 7%)
    sigma : float : Implied Volatility (e.g. 0.15 for 15%)
    option_type : str : "call" or "put"
    
    Returns:
    dict : Option Price and Greeks (Delta, Gamma, Theta, Vega, Rho)
    """
    # Guard against extremely small T
    T = max(T, 0.00001)
    # Guard against zero volatility
    sigma = max(sigma, 0.0001)
    
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    # Cumulative distribution and probability density functions
    N_d1 = si.norm.cdf(d1)
    N_d2 = si.norm.cdf(d2)
    n_prime_d1 = si.norm.pdf(d1)
    
    if option_type.lower() == "call":
        price = S * N_d1 - K * np.exp(-r * T) * N_d2
        delta = N_d1
        theta = - (S * n_prime_d1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * N_d2
        rho = K * T * np.exp(-r * T) * N_d2
    else:
        price = K * np.exp(-r * T) * si.norm.cdf(-d2) - S * si.norm.cdf(-d1)
        delta = N_d1 - 1.0
        theta = - (S * n_prime_d1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * si.norm.cdf(-d2)
        rho = -K * T * np.exp(-r * T) * si.norm.cdf(-d2)
        
    gamma = n_prime_d1 / (S * sigma * np.sqrt(T))
    vega = S * np.sqrt(T) * n_prime_d1
    
    # Scale Greeks to daily theta and standard contract sizes if needed
    return {
        "price": float(price),
        "delta": float(delta),
        "gamma": float(gamma),
        "theta": float(theta / 365.0), # Standard daily decay scale
        "vega": float(vega / 100.0),   # 1% volatility change scale
        "rho": float(rho / 100.0)      # 1% rate change scale
    }

def calculate_implied_volatility(market_price, S, K, T, r, option_type="call", max_iter=100, tolerance=0.0001):
    """
    Calculate Implied Volatility using Newton-Raphson numerical optimization
    """
    sigma = 0.20 # Starting guess (20%)
    for i in range(max_iter):
        greeks = bsm_greeks(S, K, T, r, sigma, option_type)
        diff = greeks["price"] - market_price
        
        if abs(diff) < tolerance:
            return float(sigma)
            
        # Vega represents the derivative of option price with respect to volatility
        # Convert vega back to original scale (unscaled by 100)
        vega = greeks["vega"] * 100.0
        
        if vega < 0.0001:
            # Shift slightly to avoid division by zero or flat derivative
            sigma += 0.05
            continue
            
        sigma -= diff / vega
        
        # Keep volatility bounded
        if sigma <= 0.001:
            sigma = 0.001
        if sigma > 3.0:
            sigma = 3.0
            
    return float(sigma)

# ==============================================================================
# 2. MAX PAIN ALGORITHM (EXCHANGE STRIKE OPTIMIZER)
# ==============================================================================

def calculate_max_pain(strikes, call_oi, put_oi):
    """
    Calculate the Max Pain point for option expiry where option sellers lose the least amount of capital.
    
    Parameters:
    strikes : list of float : Available option strike prices
    call_oi : list of float : Open Interest for Calls at corresponding strike
    put_oi : list of float : Open Interest for Puts at corresponding strike
    
    Returns:
    dict : Calculated Max Pain point, expected expiry range, and aggregated pain levels
    """
    df = pd.DataFrame({
        'strike': strikes,
        'call_oi': call_oi,
        'put_oi': put_oi
    }).sort_values('strike').reset_index(drop=True)
    
    pain_levels = []
    
    # For each strike price, evaluate total loss of call & put sellers if index expires AT that strike
    for target_strike in df['strike']:
        # Call sellers loss: Only options with Strike < Target Strike are in-the-money
        call_loss = 0.0
        calls_itm = df[df['strike'] < target_strike]
        if not calls_itm.empty:
            call_loss = np.sum((target_strike - calls_itm['strike']) * calls_itm['call_oi'])
            
        # Put sellers loss: Only options with Strike > Target Strike are in-the-money
        put_loss = 0.0
        puts_itm = df[df['strike'] > target_strike]
        if not puts_itm.empty:
            put_loss = np.sum((puts_itm['strike'] - target_strike) * puts_itm['put_oi'])
            
        total_pain = call_loss + put_loss
        pain_levels.append(float(total_pain))
        
    df['total_pain'] = pain_levels
    
    # Locate index with minimum aggregated pain
    min_pain_idx = df['total_pain'].idxmin()
    max_pain_strike = df.loc[min_pain_idx, 'strike']
    
    # Calculate a probable expiry range based on one standard deviation of the pain bell curve
    sorted_pain = df.sort_values('total_pain').reset_index(drop=True)
    best_strikes = sorted_pain['strike'].head(3).tolist()
    expected_low = min(best_strikes)
    expected_high = max(best_strikes)
    
    # Fallback to range bracket if they are too tight
    if expected_low == expected_high:
        idx = df[df['strike'] == max_pain_strike].index[0]
        lower_idx = max(0, idx - 2)
        upper_idx = min(len(df) - 1, idx + 2)
        expected_low = df.loc[lower_idx, 'strike']
        expected_high = df.loc[upper_idx, 'strike']
        
    return {
        "max_pain": float(max_pain_strike),
        "expected_range_low": float(expected_low),
        "expected_range_high": float(expected_high),
        "pain_chart_data": df[['strike', 'total_pain']].to_dict(orient='records')
    }

# ==============================================================================
# 3. STRATEGY PAYOFF GRAPH CALCULATOR
# ==============================================================================

def calculate_strategy_payoff(legs, price_range):
    """
    Calculate profit and loss values over a range of stock prices at expiration
    
    Parameters:
    legs : list of dict : Option legs. Format of each leg:
           {
               'strike': float,
               'premium': float,
               'type': str : 'call' or 'put',
               'side': str : 'buy' or 'sell',
               'qty': int
           }
    price_range : list of float : Underling price coordinates to plot
    
    Returns:
    dict : Aggregated payoff values, maximum profit, maximum loss, risk-reward ratio, and breakevens
    """
    payoff_curve = []
    
    for s_t in price_range:
        total_pnl = 0.0
        for leg in legs:
            strike = leg['strike']
            premium = leg['premium']
            qty = leg['qty']
            is_call = leg['type'].lower() == 'call'
            is_buy = leg['side'].lower() == 'buy'
            
            # Compute gross payoff per contract
            if is_call:
                gross_payoff = max(s_t - strike, 0.0)
            else:
                gross_payoff = max(strike - s_t, 0.0)
                
            # Net payoff incorporates the premium paid/collected
            if is_buy:
                net_payoff = (gross_payoff - premium) * qty
            else:
                net_payoff = (premium - gross_payoff) * qty
                
            total_pnl += net_payoff
            
        payoff_curve.append({
            "underlying_price": float(s_t),
            "pnl": float(total_pnl)
        })
        
    pnls = [p['pnl'] for p in payoff_curve]
    max_profit = max(pnls)
    max_loss = min(pnls)
    
    # Numerical calculation for Breakevens (crossings through zero line)
    breakevens = []
    for i in range(len(payoff_curve) - 1):
        p1, p2 = payoff_curve[i], payoff_curve[i+1]
        if (p1['pnl'] < 0 and p2['pnl'] >= 0) or (p1['pnl'] >= 0 and p2['pnl'] < 0):
            # Linearly interpolate exact crossing point S_T
            slope = (p2['pnl'] - p1['pnl']) / (p2['underlying_price'] - p1['underlying_price'])
            if slope != 0:
                zero_x = p1['underlying_price'] - (p1['pnl'] / slope)
                breakevens.append(round(float(zero_x), 2))
                
    # If the curve stays flat (e.g. infinite profit / infinite loss limits), replace with standard descriptors
    is_max_profit_inf = max_profit == pnls[0] or max_profit == pnls[-1] and max_profit > 1000
    is_max_loss_inf = max_loss == pnls[0] or max_loss == pnls[-1] and max_loss < -1000
    
    return {
        "payoff_data": payoff_curve,
        "max_profit": "Unlimited" if is_max_profit_inf else float(max_profit),
        "max_loss": "Unlimited" if is_max_loss_inf else float(max_loss),
        "risk_reward": "N/A" if is_max_loss_inf or is_max_profit_inf else abs(round(float(max_profit / max_loss), 2)) if max_loss != 0 else "N/A",
        "breakevens": breakevens
    }
