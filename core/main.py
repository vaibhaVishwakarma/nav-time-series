#%%
import os
import pandas as pd
import numpy as np
import warnings
from core.consolidater import consolidater
from core.update_latest_nav import update_latest_nav
from core.calculator import calculate_simple_returns , calculate_cagr_returns
from core.downloader import download_amfi_nav
warnings.simplefilter("ignore",pd.errors.DtypeWarning)
directory_check = lambda directory: (os.mkdir(directory)) if not os.path.exists(directory) else f"{directory} exists"

#%%
historical_nav_directory = "historical_nav/"
simple_returns_directory = "daily_simple_returns/"
cagr_returns_directory = "daily_cagr_returns/"
directory_check(historical_nav_directory)
directory_check(simple_returns_directory)
directory_check(cagr_returns_directory)

output_nav_file_path= os.path.join("nav_time_series.csv")
output_simple_returns_file_path= os.path.join(simple_returns_directory , f"simple_returns_as_on {pd.Timestamp.today().date()}.csv")
output_cagr_returns_file_path= os.path.join(cagr_returns_directory , f"cagr_returns_as_on {pd.Timestamp.today().date()}.csv")

daily_nav_file = download_amfi_nav()
#%%
total_df = consolidater(directory_path=historical_nav_directory,
                        output_nav_file_path=output_nav_file_path)
#%%
updated_df = update_latest_nav(historical_df=total_df,
                               historical_nav_file_path = output_nav_file_path,
                               daily_nav_file_path= daily_nav_file)
#%%
simple_returns_df = calculate_simple_returns(df=updated_df,
                               return_file_path=output_simple_returns_file_path)

cagr_returns_df = calculate_cagr_returns(df=updated_df,
                               return_file_path=output_cagr_returns_file_path)

# %%
