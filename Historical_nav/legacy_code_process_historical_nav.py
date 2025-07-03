import pandas as pd
import os
import re
from datetime import datetime

def read_mf_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    data_start_index = next(
        (i for i, line in enumerate(lines) if re.match(r'\d{6}', line.strip().split(';')[0])),
        None
    )
    
    if data_start_index is None:
        return pd.DataFrame()  
    
    data_lines = lines[data_start_index:]
    
    data = []
    for line in data_lines:
        line = line.strip()
        if line:
            parts = line.split(';')
            if len(parts) >= 8:  
                isin = parts[2].strip()  # ISIN Div Payout/ISIN Growth column
                if isin and len(isin) >= 10:  # Basic ISIN validation (most ISINs are 12 characters)
                    data.append(parts)
    
    # Create a DataFrame
    columns = [
        "Scheme Code", "Scheme Name", "ISIN Div Payout/ISIN Growth", "ISIN Div Reinvestment", 
        "Net Asset Value", "Repurchase Price", "Sale Price", "Date"
    ]
    df = pd.DataFrame(data, columns=columns)
    
    df["Scheme Code"] = pd.to_numeric(df["Scheme Code"], errors='coerce')
    df["Net Asset Value"] = pd.to_numeric(df["Net Asset Value"], errors='coerce')
    df["Repurchase Price"] = pd.to_numeric(df["Repurchase Price"], errors='coerce')
    df["Sale Price"] = pd.to_numeric(df["Sale Price"], errors='coerce')
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    
    df = df[df['ISIN Div Payout/ISIN Growth'].str.len() >= 10].copy()
    
    print(f"Total rows after filtering invalid ISINs: {len(df)}")
    
    return df.dropna(subset=["Scheme Code", "Net Asset Value", "Date", "ISIN Div Payout/ISIN Growth"])

def calculate_returns_fast(df):
    df = df.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Pivot NAVs: rows = dates, columns = scheme codes
    nav_wide = df.pivot(index='Date', columns='Scheme Code', values='Net Asset Value').sort_index()
    
    # Latest NAV
    latest_nav = nav_wide.ffill().iloc[-1]
    
    def compute_return(delta_days):
        past_date = nav_wide.index[-1] - pd.Timedelta(days=delta_days)
        past_nav = nav_wide[nav_wide.index <= past_date].ffill().iloc[-1]
        return ((latest_nav - past_nav) / past_nav * 100).round(2)
    
    # Compute returns
    returns = pd.DataFrame({
        '1W Return': compute_return(7),
        '1M Return': compute_return(30),
        '1Y Return': compute_return(365),
        '3Y Return': compute_return(3 * 365),
        '5Y Return': compute_return(5 * 365),
    })
    
    # YTD Return
    ytd_start = pd.Timestamp(nav_wide.index[-1].year, 1, 1)
    ytd_nav = nav_wide[nav_wide.index >= ytd_start].ffill().iloc[0]
    returns['YTD Return'] = ((latest_nav - ytd_nav) / ytd_nav * 100).round(2)
    
    # Total Return
    first_nav = nav_wide.ffill().iloc[0]
    returns['Total Return'] = ((latest_nav - first_nav) / first_nav * 100).round(2)
    
    # Add ISIN & Scheme Name from the latest date per scheme
    latest_meta = df.sort_values('Date').groupby('Scheme Code').last()[['Scheme Name', 'ISIN Div Payout/ISIN Growth']]
    latest_meta = latest_meta.rename(columns={'ISIN Div Payout/ISIN Growth': 'ISIN'})
    
    # Merge
    result_df = returns.merge(latest_meta, left_index=True, right_index=True)
    result_df = result_df.reset_index().sort_values('Total Return', ascending=False)
    
    # Format % strings
    return_cols = ['1W Return', '1M Return', '1Y Return', '3Y Return', '5Y Return', 'YTD Return', 'Total Return']
    for col in return_cols:
        result_df[col] = result_df[col].apply(lambda x: f"{x}%" if pd.notnull(x) else None)

    return result_df[['ISIN', 'Scheme Code', 'Scheme Name'] + return_cols]


# def calculate_returns(df):
    # results = []
    
    # for scheme_code in df['Scheme Code'].unique():
    #     scheme_df = df[df['Scheme Code'] == scheme_code].copy()
    #     scheme_df = scheme_df.sort_values(by='Date')
        
    #     latest_nav = float(scheme_df['Net Asset Value'].iloc[-1])
    #     scheme_name = scheme_df['Scheme Name'].iloc[-1]
    #     isin = scheme_df['ISIN Div Payout/ISIN Growth'].iloc[-1]  
        
    #     print(f"\nProcessing scheme: {scheme_name} ({scheme_code})")
    #     print(f"Latest NAV: {latest_nav}")
        
    #     def get_return(days):
    #         try:
    #             past_date = scheme_df['Date'].max() - pd.Timedelta(days=days)
    #             past_values = df[
    #                 (df['Scheme Code'] == scheme_code) & 
    #                 (df['Date'] <= past_date)
    #             ]['Net Asset Value']
                
    #             if past_values.empty:
    #                 return None
                    
    #             past_nav = float(past_values.iloc[-1])
    #             if past_nav == 0:
    #                 return None
                    
    #             return round(((latest_nav - past_nav) / past_nav * 100), 2)
    #         except Exception as e:
    #             print(f"Error calculating {days} day return: {str(e)}")
    #             return None
        
    #     try:
    #         ytd_start = pd.Timestamp(scheme_df['Date'].max().year, 1, 1)
    #         ytd_values = df[
    #             (df['Scheme Code'] == scheme_code) & 
    #             (df['Date'] <= ytd_start)
    #         ]['Net Asset Value']
            
    #         if ytd_values.empty:
    #             ytd_return = None
    #         else:
    #             ytd_nav = float(ytd_values.iloc[-1])
    #             if ytd_nav == 0:
    #                 ytd_return = None
    #             else:
    #                 ytd_return = round(((latest_nav - ytd_nav) / ytd_nav * 100), 2)
    #     except Exception as e:
    #         print(f"Error calculating YTD return: {str(e)}")
    #         ytd_return = None
        
    #     try:
    #         first_nav = float(scheme_df['Net Asset Value'].iloc[0])
    #         if first_nav == 0:
    #             total_return = None
    #         else:
    #             total_return = round(((latest_nav - first_nav) / first_nav * 100), 2)
    #     except Exception as e:
    #         print(f"Error calculating total return: {str(e)}")
    #         total_return = None
        
    #     result = {
    #         'ISIN': isin,  
    #         'Scheme Code': scheme_code,
    #         'Scheme Name': scheme_name,
    #         '1W Return': get_return(7),
    #         '1M Return': get_return(30),
    #         '1Y Return': get_return(365),
    #         '3Y Return': get_return(3 * 365),
    #         '5Y Return': get_return(5 * 365),  
    #         'YTD Return': ytd_return,
    #         'Total Return': total_return
    #     }
        
    #     print(f"Calculated returns: {result}")
    #     results.append(result)
    
    # df_results = pd.DataFrame(results)
    
    # df_results = df_results.sort_values('Total Return', ascending=False)
    
    # return_columns = ['1W Return', '1M Return', '1Y Return', '3Y Return', '5Y Return', 'YTD Return', 'Total Return']  # Added 5Y Return
    # for col in return_columns:
    #     df_results[col] = df_results[col].apply(lambda x: f"{x}%" if pd.notnull(x) else x)
    
    # return df_results

# def create_top_performers_sheet(returns_df, writer, period_column, sheet_name, top_n=20):
#     df_copy = returns_df.copy()
#     df_copy[period_column] = df_copy[period_column].str.rstrip('%').astype(float)
    
#     top_performers = df_copy[['ISIN', 'Scheme Code', 'Scheme Name', period_column]]\
#         .sort_values(period_column, ascending=False)\
#         .head(top_n)
    
#     top_performers.to_excel(writer, sheet_name=sheet_name, index=False)

# def extract_amc_name(scheme_name):
#     if scheme_name.startswith("Parag Parikh"):
#         return "Parag Parikh"
#     elif scheme_name.startswith("Aditya Birla Sun"):
#         return "Aditya Birla Sun"
#     else:
#         return scheme_name.split(" ")[0]

# def create_amc_wise_top_performers(returns_df, writer, period_column, sheet_name_prefix):
#     df_copy = returns_df.copy()
#     df_copy['AMC'] = df_copy['Scheme Name'].apply(extract_amc_name)
    
 
#     df_copy[period_column] = df_copy[period_column].str.rstrip('%').astype(float)
    
#     amcs = sorted(df_copy['AMC'].unique())
    
#     summary_rows = []
    
#     for amc in amcs:
#         amc_df = df_copy[df_copy['AMC'] == amc]
        

#         top_performer = amc_df.nlargest(1, period_column)
#         if not top_performer.empty:
#             summary_rows.append({
#                 'AMC': amc,
#                 'ISIN': top_performer['ISIN'].iloc[0],  
#                 'Top Scheme': top_performer['Scheme Name'].iloc[0],
#                 'Return': f"{top_performer[period_column].iloc[0]}%"
#             })
    
#     summary_df = pd.DataFrame(summary_rows)
#     summary_df['Sort_Value'] = summary_df['Return'].str.rstrip('%').astype(float)
#     summary_df = summary_df.sort_values('Sort_Value', ascending=False)
#     summary_df = summary_df.drop('Sort_Value', axis=1)

#     sheet_name = f"{sheet_name_prefix} by AMC"
#     if len(sheet_name) > 31:  
#         sheet_name = sheet_name[:31]
#     summary_df.to_excel(writer, sheet_name=sheet_name, index=False)

def process_multiple_files(directory):
    all_data = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            print(f"\nReading file: {file_path}")
            df = read_mf_data(file_path)
            if not df.empty:
                all_data.append(df)
    
    if all_data:
        consolidated_df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal records before grouping: {len(consolidated_df)}")
        
        print(consolidated_df.info())
        consolidated_df = consolidated_df.sort_values('Date')
        
        print(f"Date range in data: {consolidated_df['Date'].min()} to {consolidated_df['Date'].max()}")
        
        return consolidated_df
    return pd.DataFrame()

start_time = datetime.now()
print(f"Processing started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

directory_path = "Historical_nav/"

consolidated_df = process_multiple_files(directory_path)
print(f"\nNumber of unique schemes: {len(consolidated_df['Scheme Code'].unique())}")
returns_df = calculate_returns_fast(consolidated_df)


excel_path_1 = os.path.join(directory_path, "nav_time_series.csv")
consolidated_df.to_csv(excel_path_1, index=False)

excel_path = os.path.join(directory_path, "historical_nav_returns.csv")
returns_df.to_csv(excel_path, index=False)
    

"""
# write top performers for different periods

period_sheets = {
    '1W Return': 'Top 1 Week',
    '1M Return': 'Top 1 Month',
    '1Y Return': 'Top 1 Year',
    '3Y Return': 'Top 3 Years',
    '5Y Return': 'Top 5 Years',
    'YTD Return': 'Top YTD',
    'Total Return': 'Top Total Return'
}

for period_col, sheet_name in period_sheets.items():
    create_top_performers_sheet(returns_df, writer, period_col, sheet_name)
    create_amc_wise_top_performers(returns_df, writer, period_col, sheet_name)
"""
end_time = datetime.now()
processing_time = end_time - start_time

print("\nProcessing completed!")
print(f"Total processing time: {processing_time}")
# %%
