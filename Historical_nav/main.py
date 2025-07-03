#%%
import os
import pandas as pd
import numpy as np
import warnings
from consolidater import consolidater
from update_latest_nav import update_latest_nav
from calculator import calculate_returns
warnings.simplefilter("ignore",pd.errors.DtypeWarning)
#%%
directory_path = "./"
output_nav_file_path= os.path.join( directory_path , "nav_time_series.csv")
daily_nav_file = r"../dailyNAV/NAVAll_2025-07-02.txt" 
#%%
total_df = consolidater(directory_path, output_nav_file_path=output_nav_file_path)
#%%
updated_df = update_latest_nav(historical_df=total_df,
                               historical_nav_file_path = output_nav_file_path,
                               daily_nav_file_path= daily_nav_file)
#%%
returns_df = calculate_returns(updated_df, os.path.join(directory_path,"returns.csv"))
