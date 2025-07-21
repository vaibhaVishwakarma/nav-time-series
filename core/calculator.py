#%%
import pandas as pd
import numpy as np
import os

# df = pd.read_csv("nav_time_series.csv",delimiter=";").dropna()
# return_file_path = "returns_test.csv"

ROUND_DECIMALS = 6 

def calculate_returns(df, return_file_path="returns_simple.csv"):
    DELTA_DAYS = int(os.environ.get("DELTA_DAYS",0))
    TODAY= pd.Timestamp.today().date() - pd.Timedelta(days=DELTA_DAYS)
    
    df = df.copy()
    df['Date'] = df['Date'].apply(lambda x: pd.Timestamp(x).date())
    # Step 1: Aggregate duplicate NAV entries (use mean or last as needed)
    df_grouped = df.groupby(['Date', 'Scheme Code'], as_index=False)['Net Asset Value'].mean()
    # Step 2: Pivot NAVs: rows = dates, columns = scheme codes
    nav_wide = df_grouped.pivot(index='Date', columns='Scheme Code', values='Net Asset Value').sort_index()
    # Step 3: Get latest NAV (forward fill missing NAVs)
    nav_wide = nav_wide.ffill()
    _latest_date = nav_wide.index[-1]
    if(_latest_date > TODAY):
        if TODAY not in nav_wide.index:
            nav_wide.loc[TODAY] = pd.NA
            nav_wide = nav_wide.sort_index().ffill()
        _latest_date = TODAY
        
    latest_nav = nav_wide.loc[_latest_date]

    formula_simple = lambda latest_nav, past_nav : round(((latest_nav - past_nav) / past_nav * 100), ROUND_DECIMALS)
    formula_cagr = lambda latest_nav, past_nav, years : round(((latest_nav / past_nav) ** (1 / years) - 1) *100, ROUND_DECIMALS)

    debug_isin = None

    def compute_return_simple(delta_days, nav_wide):
        past_date = TODAY - pd.Timedelta(days=delta_days)
        if past_date < nav_wide.index[0]:
            return pd.Series([None] * len(latest_nav), index=latest_nav.index)
        if past_date not in nav_wide.index:
            nav_wide.loc[past_date] = pd.NA
            nav_wide = nav_wide.sort_index().ffill()
        past_nav = nav_wide.loc[past_date]

        ret =  formula_simple(latest_nav , past_nav)
        if debug_isin:
            print(past_date)
            print(past_nav.loc[debug_isin])
            print(ret.loc[debug_isin])
            print(latest_nav.loc[debug_isin])
        return ret
    
    def compute_return_cagr(delta_days, nav_wide):
        years = delta_days/365
        past_date = TODAY - pd.Timedelta(days=delta_days)
        if past_date < nav_wide.index[0]:
            return pd.Series([None] * len(latest_nav), index=latest_nav.index)
        if past_date not in nav_wide.index:
            nav_wide.loc[past_date] = pd.NA
            nav_wide = nav_wide.sort_index().ffill()
        past_nav = nav_wide.loc[past_date]
        ret = formula_cagr(latest_nav, past_nav, years)
        if debug_isin:
            print(past_date)
            print(past_nav.loc[debug_isin])
            print(ret.loc[debug_isin])
            print(latest_nav.loc[debug_isin])
        return ret

    

    returns = pd.DataFrame({
        'return_1m': compute_return_simple(30,nav_wide),
        'return_3m': compute_return_simple(3*30,nav_wide),
        'return_6m': compute_return_simple(6*30,nav_wide),
        'return_1y': compute_return_simple(365,nav_wide),
        'return_3y': compute_return_simple(3 * 365,nav_wide),
        'return_5y': compute_return_simple(5 * 365,nav_wide),

        'return_1y_cagr': compute_return_cagr(365, nav_wide),
        'return_3y_cagr': compute_return_cagr(3 * 365, nav_wide),
        'return_5y_cagr': compute_return_cagr(5 * 365, nav_wide),
        'return_10y_cagr': compute_return_cagr(10* 365, nav_wide),
    })

    # YTD
    current_year_start = pd.Timestamp(f"{pd.Timestamp.today().year}-01-01").date()
    today = TODAY
    days = (today - current_year_start).days
    returns["return_ytd"] = compute_return_simple(days, nav_wide)
    returns["return_ytd_cagr"] = compute_return_cagr(days, nav_wide)

    # total returns - since the day of first record
    first_indexes = nav_wide.apply(lambda col: col.first_valid_index())
    first_values = pd.Series({col: nav_wide.at[idx, col] for col, idx in first_indexes.items()})
    today = TODAY
    # print(first_indexes[153324])
    # print(first_values[153324])
    # print(first_indexes.apply(lambda d: (today - d).days).loc[153324])
    # print(latest_nav[153324])
    delta_years =first_indexes.apply(lambda d: (today - d).days) / 365

    returns["return_since_inception"] = formula_simple(latest_nav, first_values)
    returns["return_since_inception_cagr"] = formula_cagr(latest_nav, first_values, delta_years)


    # Merge with metadata (Scheme Name + ISINs)
    latest_meta = df.sort_values('Date').groupby('Scheme Code').last()[[
        'Scheme Name', 'ISIN Div Payout/ISIN Growth', 'ISIN Div Reinvestment'
    ]]

    # Merge returns with metadata
    result_df = returns.merge(latest_meta, left_index=True, right_index=True)
    result_df = result_df.reset_index()  # Scheme Code becomes column again
    # Sort by Total Return
    result_df = result_df.sort_values('return_since_inception_cagr', ascending=False)

    # Format return values as percentage strings
    return_cols = ['return_1m','return_3m', 'return_6m', 'return_1y','return_3y','return_5y', 'return_ytd', 'return_ytd_cagr','return_1y_cagr','return_3y_cagr', 'return_5y_cagr', 'return_10y_cagr','return_since_inception','return_since_inception_cagr']

    # Arrange final column order
    final_cols = [
        'ISIN Div Payout/ISIN Growth', 'ISIN Div Reinvestment',
        'Scheme Code', 'Scheme Name'
    ] + return_cols

    total_returns_df = result_df[final_cols]
    total_returns_df = total_returns_df[~total_returns_df.duplicated(subset=["ISIN Div Payout/ISIN Growth"], keep=False)]
    # Save to CSV using semicolon as delimiter
    total_returns_df.to_csv(return_file_path, index=False, sep=";")

    return total_returns_df
