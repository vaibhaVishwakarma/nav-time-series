import requests
from datetime import datetime
import os
import pandas as pd


def download_amfi_nav(output_dir="daily_nav"):
    DELTA_DAYS = int(os.environ.get("DELTA_DAYS",0))

    # AMFI daily NAV data URL
    amfi_url = "https://www.amfiindia.com/spages/NAVAll.txt"
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    # Create a timestamped filename
    today = pd.Timestamp.today().date() - pd.Timedelta(days=DELTA_DAYS)
    file_path = os.path.join(output_dir, f"NAVAll_{today}.txt")
    try:
        print(f"Downloading NAV data for {today}...")
        response = requests.get(amfi_url, timeout=30)
        response.raise_for_status()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"NAV data saved to {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download AMFI NAV data: {e}")
    return file_path
if __name__ == "__main__":
    download_amfi_nav()
