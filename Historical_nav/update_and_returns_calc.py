# expected to run in the same folder as text files
#%%
import os
import pandas as pd
import numpy as np
import warnings

from update_latest_nav import update_latest_nav
from calculator import calculate_returns
warnings.simplefilter("ignore",pd.errors.DtypeWarning)

#%%
directory_path = "./"
output_nav_file_path= os.path.join( directory_path , "nav_time_series.csv")
daily_nav_file = r"../dailyNAV/NAVAll_2025-07-01.txt" 

#%%
historical_df = pd.read_csv(output_nav_file_path,delimiter=";").dropna()

#%%
updated_df = update_latest_nav(historical_df=historical_df,
                               historical_nav_file_path = output_nav_file_path,
                               daily_nav_file_path= daily_nav_file)
#%%
returns_df = calculate_returns(updated_df, os.path.join(directory_path,"returns.csv"))

# %%
