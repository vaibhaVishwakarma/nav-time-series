from core.daily_calc import task
from SQL.setup_db import db, create_app
from SQL.returnstosql import upsert
import sys
import io
import os
from dotenv import load_dotenv
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv(dotenv_path="./.env")

print("- "*60)

os.environ["DELTA_DAYS"] = os.getenv("DELTA_DAYS",0)
DELTA_DAYS = int(os.environ.get("DELTA_DAYS",0))
print("DELTA_DAYS= ",os.environ.get("DELTA_DAYS",0))

def main():
    """the program is designed to only calculate for the present day.
        to load any previous data the `core.nav_history_downloader` need execution followed by `main_runner`"""

    app = create_app()  # Create the Flask app instance
    status = True

    historical_nav_directory = "historical_nav/"
    returns_directory = "daily_returns/"
    
    status = task(historical_nav_directory=historical_nav_directory,
                  returns_directory=returns_directory)    

    if not status:
        print("[Error]: ❌ Task Failed")
        return
    
    try:
        with app.app_context():  # Push application context 
            upsert(returns_directory=returns_directory)
    except Exception as e:
        print("[Error]: ❌ Task Failed\n",e.__traceback__.tb_lineno,e)
        return

    print("✅ task completed without error")   

    with open("last_updated.txt", "w") as f:
        target_date = (pd.Timestamp.today() - pd.Timedelta(days=DELTA_DAYS)).date()
        f.write(str(target_date))
    
main()

# %%
