# expected to run in the same folder as text files
#%%
import os
import pandas as pd
import numpy as np
import warnings

from core.update_latest_nav import update_latest_nav
from core.calculator import calculate_returns
from core.downloader import download_amfi_nav
warnings.simplefilter("ignore",pd.errors.DtypeWarning)


#%%

def task(   historical_nav_directory = "historical_nav/",
            returns_directory = "daily_returns/",
            ):
    try:
        directory_check = lambda directory: os.makedirs(directory, exist_ok=True)
        directory_check(historical_nav_directory)
        directory_check(returns_directory)
        
        nav_file_path = "nav_time_series.csv"

        output_returns_file_path= os.path.join(returns_directory , f"returns_as_on {pd.Timestamp.today().date()}.csv")
        

        daily_nav_file = download_amfi_nav()
        #%%
        historical_df = pd.DataFrame()
        if os.path.exists(nav_file_path):
            historical_df = pd.read_csv(nav_file_path,delimiter=";").dropna()     

        #%%
        updated_df = update_latest_nav(historical_df=historical_df,
                                    historical_nav_file_path = nav_file_path,
                                    daily_nav_file_path= daily_nav_file)
        #%%
        returns_df = calculate_returns(df=updated_df,
                                    return_file_path=output_returns_file_path)
    
        return True
    except Exception as e:
        print("[Error]: ",e)
        return False

# %%
if __name__ == "__main__":
    task()