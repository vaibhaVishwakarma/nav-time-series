# nav-time-series  
### TODO
- [X] CAGR calculations
- [X] remake to cron job
### How to run
```shell 
# CRON Job start
python -m job
```
```shell 
# to compile all Historical NAVs > update based on current NAVs > calculate returns
python -m core.main
```
```shell 
# to update based on current NAVs > calculate returns
python -m core.daily_calc
```
### CORE Structure  
---
|   nav_time_series.csv    
|  
\+ core  
|   | calculator.py  
|   |    consolidater.py  
|   |    downloader.py  
|   |    main.py  
|   |    update_and_returns_calc.py  
|   |    update_latest_nav.py  
|   |    main_run.log  
|   |    last_updated.txt  
|  
\+ daily_nav  
|   | NAVAll_2025-06-27.txt  
|  
\+ daily_simple_returns  
|   | simple_returns_as_on 2025-07-04.csv  
|  
\+ daily_cagr_returns  
|   | cagr_returns_as_on 2025-07-04.csv  
|  
\+ historical_nav  
|   | DownloadNAVHistoryMotilaloswal.txt  
        
---  
