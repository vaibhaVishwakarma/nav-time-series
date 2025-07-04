#%%
import pandas as pd
import numpy as np

# df = pd.read_csv("nav_time_series.csv",delimiter=";").dropna()
# return_file_path = "returns_test.csv"

ROUND_DECIMALS = 6 


def calculate_simple_returns(df, return_file_path="returns_simple.csv"):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    # Step 1: Aggregate duplicate NAV entries (use mean or last as needed)
    df_grouped = df.groupby(['Date', 'Scheme Code'], as_index=False)['Net Asset Value'].mean()
    # Step 2: Pivot NAVs: rows = dates, columns = scheme codes
    nav_wide = df_grouped.pivot(index='Date', columns='Scheme Code', values='Net Asset Value').sort_index()
    # Step 3: Get latest NAV (forward fill missing NAVs)
    nav_wide = nav_wide.ffill()
    latest_nav = nav_wide.iloc[-1]
    # Step 4: Return computation function
    def compute_return(delta_days):
        past_date = nav_wide.index[-1] - pd.Timedelta(days=delta_days)
        if past_date < nav_wide.index[0]:
            return pd.Series([None] * len(latest_nav), index=latest_nav.index)
        past_nav = nav_wide.loc[:past_date].iloc[-1]
        return round(((latest_nav - past_nav) / past_nav * 100), ROUND_DECIMALS)
    # Step 5: Compute period returns SIMPLE
    returns = pd.DataFrame({
        '1W Return': compute_return(7),
        '1M Return': compute_return(30),
        '1Y Return': compute_return(365),
        '3Y Return': compute_return(3 * 365),
        '5Y Return': compute_return(5 * 365),
    })

    # Step 6: Year-To-Date Return
    current_year_start = pd.Timestamp(f"{pd.Timestamp.today().year}-01-01")
    if current_year_start > nav_wide.index[0]:
        ytd_nav = nav_wide.loc[:current_year_start].iloc[-1]
        # print(nav_wide.loc[:current_year_start])
        returns['YTD Return'] = round(((latest_nav - ytd_nav) / ytd_nav * 100), ROUND_DECIMALS)
    else:
        returns['YTD Return'] = None
    # Step 7: Total Return from first available NAV
    first_nav = nav_wide.iloc[0]
    returns['Total Return'] = round(((latest_nav - first_nav) / first_nav * 100), ROUND_DECIMALS)
    # Step 8: Merge with metadata (Scheme Name + ISINs)
    latest_meta = df.sort_values('Date').groupby('Scheme Code').last()[[
        'Scheme Name', 'ISIN Div Payout/ISIN Growth', 'ISIN Div Reinvestment'
    ]]
    # Step 9: Merge returns with metadata
    result_df = returns.merge(latest_meta, left_index=True, right_index=True)
    result_df = result_df.reset_index()  # Scheme Code becomes column again
    # Step 10: Sort by Total Return
    result_df = result_df.sort_values('Total Return', ascending=False)

    # Step 11: Format return values as percentage strings
    return_cols = ['1W Return', '1M Return', '1Y Return', '3Y Return', '5Y Return', 'YTD Return', 'Total Return']

    # Step 12: Arrange final column order
    final_cols = [
        'ISIN Div Payout/ISIN Growth', 'ISIN Div Reinvestment',
        'Scheme Code', 'Scheme Name'
    ] + return_cols

    total_returns_df = result_df[final_cols]
    total_returns_df = total_returns_df[~total_returns_df.duplicated(subset=["ISIN Div Payout/ISIN Growth"], keep=False)]
    # Step 13: Save to CSV using semicolon as delimiter
    total_returns_df.to_csv(return_file_path, index=False, sep=";")

    return total_returns_df

def calculate_cagr_returns(df, return_file_path="returns_cagr.csv"):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    # Step 1: Aggregate duplicate NAV entries (use mean or last as needed)
    df_grouped = df.groupby(['Date', 'Scheme Code'], as_index=False)['Net Asset Value'].mean()
    # Step 2: Pivot NAVs: rows = dates, columns = scheme codes
    nav_wide = df_grouped.pivot(index='Date', columns='Scheme Code', values='Net Asset Value').sort_index()
    # Step 3: Get latest NAV (forward fill missing NAVs)
    nav_wide = nav_wide.ffill()
    latest_nav = nav_wide.iloc[-1]
    # Step 4: Return computation function CAGR 

    def compute_return(delta_days):
        years = delta_days/365
        past_date = nav_wide.index[-1] - pd.Timedelta(days=delta_days)
        if past_date < nav_wide.index[0]:
            return pd.Series([None] * len(latest_nav), index=latest_nav.index)
        past_nav = nav_wide.loc[:past_date].iloc[-1]
        cagr = (latest_nav / past_nav) ** (1 / years) - 1
        return round(cagr * 100, ROUND_DECIMALS)
    # Step 5: Compute period returns
    returns = pd.DataFrame({
        '1W Return': compute_return(7),
        '1M Return': compute_return(30),
        '1Y Return': compute_return(365),
        '3Y Return': compute_return(3 * 365),
        '5Y Return': compute_return(5 * 365),
    })

    # Step 6: Year-To-Date Return
    current_year_start = pd.Timestamp(f"{pd.Timestamp.today().year}-01-01")
    if current_year_start > nav_wide.index[0]:
        ytd_nav = nav_wide.loc[:current_year_start].iloc[-1]
        first_day_of_year = pd.Timestamp(f"{pd.Timestamp.today().year}-01-01")
        years = (today - first_day_of_year).days / 365
        today = pd.Timestamp.today()
        # print(nav_wide.loc[:current_year_start])
        returns['YTD Return'] = round((((latest_nav / ytd_nav) ** (1 / years)  - 1)* 100), ROUND_DECIMALS)
    else:
        returns['YTD Return'] = None
    # Step 7: Total Return from first available NAV
    first_nav = nav_wide.iloc[0]
    beggining = nav_wide.index[0]
    today = pd.Timestamp.today()
    years = (today - beggining).days / 365
    
    returns['Total Return'] = round(((latest_nav / first_nav) ** (1 / years) - 1), ROUND_DECIMALS)
    # Step 8: Merge with metadata (Scheme Name + ISINs)
    latest_meta = df.sort_values('Date').groupby('Scheme Code').last()[[
        'Scheme Name', 'ISIN Div Payout/ISIN Growth', 'ISIN Div Reinvestment'
    ]]
    # Step 9: Merge returns with metadata
    result_df = returns.merge(latest_meta, left_index=True, right_index=True)
    result_df = result_df.reset_index()  # Scheme Code becomes column again
    # Step 10: Sort by Total Return
    result_df = result_df.sort_values('Total Return', ascending=False)

    # Step 11: Format return values as percentage strings
    return_cols = ['1W Return', '1M Return', '1Y Return', '3Y Return', '5Y Return', 'YTD Return', 'Total Return']

    # Step 12: Arrange final column order
    final_cols = [
        'ISIN Div Payout/ISIN Growth', 'ISIN Div Reinvestment',
        'Scheme Code', 'Scheme Name'
    ] + return_cols

    total_returns_df = result_df[final_cols]
    total_returns_df = total_returns_df[~total_returns_df.duplicated(subset=["ISIN Div Payout/ISIN Growth"], keep=False)]
    # Step 13: Save to CSV using semicolon as delimiter
    total_returns_df.to_csv(return_file_path, index=False, sep=";")

    return total_returns_df

