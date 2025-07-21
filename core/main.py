#%%
import os
import pandas as pd
import numpy as np
import warnings
from core.consolidater import consolidater
from core.update_latest_nav import update_latest_nav
from core.calculator import calculate_returns
from core.downloader import download_amfi_nav
warnings.simplefilter("ignore",pd.errors.DtypeWarning)
directory_check = lambda directory: (os.mkdir(directory)) if not os.path.exists(directory) else f"{directory} exists"

#%%

DELTA_DAYS = int(os.environ.get("DELTA_DAYS",0))

historical_nav_directory = "historical_nav/"
returns_directory = "daily_returns/"
directory_check(historical_nav_directory)
directory_check(returns_directory)

output_nav_file_path= os.path.join("nav_time_series.csv")

date=pd.Timestamp.today().date() - pd.Timedelta(days=DELTA_DAYS)
output_returns_file_path= os.path.join(returns_directory , f"returns_as_on {date}.csv")

daily_nav_file = download_amfi_nav()
#%%
total_df = consolidater(directory_path=historical_nav_directory,
                        output_nav_file_path=output_nav_file_path)
#%%
updated_df = update_latest_nav(historical_df=total_df,
                               historical_nav_file_path = output_nav_file_path,
                               daily_nav_file_path= daily_nav_file)
#%%
returns_df = calculate_returns(df=updated_df,
                               return_file_path=output_returns_file_path)



# %%
