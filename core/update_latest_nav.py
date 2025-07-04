#%%
import os
import pandas as pd
import numpy as np
from core.consolidater import consolidater
def check_last_updated(date = "" , file_path="last_updated.txt"):
    last_updated_str = ""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            last_updated_str = f.read().strip()
    else:
        last_updated_str = date

    with open(file_path, "w") as f:
        f.write(date)
    
    return last_updated_str

def update_latest_nav(historical_df, daily_nav_file_path=r"../dailyNAV/NAVAll_2025-06-29.txt", historical_nav_file_path="nav_time_series.csv"):
    date = daily_nav_file_path.split("_")[-1].split(".txt")[0]
    last_update_date = check_last_updated(date)
    print("skipping updates as last updated for same day")
    if last_update_date == date:
        return historical_df

    df = pd.read_csv(daily_nav_file_path , delimiter=";")[["Scheme Code" , "Scheme Name", "ISIN Div Payout/ ISIN Growth", "ISIN Div Reinvestment", "Net Asset Value" , "Date"]]
    df = df.drop(df[~df["Scheme Code"].fillna("-").astype(str).apply(lambda x : x.isdigit())].index)
    df["Scheme Code"] = df["Scheme Code"].astype(int)
    df["Net Asset Value"] = df["Net Asset Value"].replace("N.A." , np.nan).fillna("0").astype(np.float64)

    df["Date"] = pd.to_datetime(df["Date"], errors = "coerce")
    df = df[df["Date"].dt.date ==  pd.to_datetime(date).date() - pd.Timedelta(days=1)] # day = 3 processes 27 if today is 30
    df["Date"] = df["Date"].dt.strftime('%Y-%m-%d')
    df["ISIN Div Reinvestment"] = df["ISIN Div Reinvestment"].replace("-","")
    df["ISIN Div Payout/ ISIN Growth"] = df["ISIN Div Payout/ ISIN Growth"].replace("-","")


    data_to_store = ""

    for (idx , row) in df.iterrows():
        row_data = ";".join(row.astype(str).values.tolist())
        data_to_store += row_data + "\n"

    start_char = "\n"
    with open(historical_nav_file_path , "r") as f :
        f.seek(0, 2)  # Move the file pointer to the end of the file
        file_size = f.tell()

        if file_size > 0:
            f.seek(file_size - 1, 0)  # Move the file pointer back one byte from the end
            last_char = f.read(1)  # Read one character
            if last_char == "\n": start_char = ""

    if(data_to_store == "") : print("Nothing to store today")
    with open(historical_nav_file_path , "a") as f :
        f.write(start_char+data_to_store)

    return pd.concat([historical_df, df])


#%%
if __name__ == "__main__":
    #%%
    total_df = consolidater()
    historical_nav_file_path = "nav_time_series.csv"
    #%%
    daily_nav_file = r"../dailyNAV/NAVAll_2025-06-29.txt"
    updated_df = update_latest_nav(historical_df=total_df, daily_nav_file_path=daily_nav_file , historical_nav_file_path=historical_nav_file_path)
    # print(updated_df.head(10))
# %%
