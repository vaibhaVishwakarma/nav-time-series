import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
import os
import re
import html

directoy_path = "historical_nav"

url = "https://www.amfiindia.com/net-asset-value/nav-history"

res = requests.get(url)

soup = BeautifulSoup(res.text, "html.parser")

mfs = soup.find(id="NavHisMFName").find_all("option")

mfs = pd.Series(list(map(lambda x : (x["value"], x.text),mfs)))

mfs = mfs[mfs.apply(lambda x : x[0].isalnum())]

DELTA_DAYS = int(os.environ.get("DELTA_DAYS",0))
today = (pd.Timestamp.today() - pd.Timedelta(days=DELTA_DAYS)).date()
back_10y = today - pd.Timedelta(days= 10*365+3)
back_5y = today - pd.Timedelta(days= 5*365+2)
back_3y = today - pd.Timedelta(days= 3*365+1)
back_1y = today - pd.Timedelta(days= 1*365+1)
start_10y, start_5y, start_3y, start_1y, end = (back_10y.strftime("%d-%b-%Y"),
                                    back_5y.strftime("%d-%b-%Y"),
                                    back_3y.strftime("%d-%b-%Y"),
                                    back_1y.strftime("%d-%b-%Y"),
                                    today.strftime("%d-%b-%Y"))
url_string = lambda mf_code, start, end : f"https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?mf={mf_code}&frmdt={start}&todt={end}"


def save_to_text(mf_name, data):
    mf_name = re.sub(" ", "_" ,mf_name) + ".txt"
    file_path = os.path.join(directoy_path, mf_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html.unescape(str(data)))
        
    print(f"✅ done - {mf_name}")
    return True

def handle_get(url):
    try:
        res = requests.get(url, timeout=40)
        if res.ok:
            return res
    except Exception as e:
        pass
    return False


def get_nav_data(pair):
    mf_code, mf_name = pair
    time.sleep(1.5)
 
    not_found_string = "No data found on the basis of selected parameters for this report"
    url = url_string(mf_code = mf_code, start = start_10y, end=end)
    res = handle_get(url)
    if res and not_found_string not in res.text:
        return save_to_text(mf_name, BeautifulSoup(res.text, "html.parser"))
    url = url_string(mf_code = mf_code, start = start_5y, end=end)
    res = handle_get(url)
    if res and not_found_string not in res.text:
        return save_to_text(mf_name, BeautifulSoup(res.text, "html.parser"))
    url = url_string(mf_code = mf_code, start = start_3y, end=end)
    res = handle_get(url)
    if res and not_found_string not in res.text:
        return save_to_text(mf_name, BeautifulSoup(res.text, "html.parser"))
    url = url_string(mf_code = mf_code, start = start_1y, end=end)
    res = handle_get(url)
    if res and not_found_string not in res.text:
        return save_to_text(mf_name, BeautifulSoup(res.text, "html.parser"))
    return False

mfs= mfs
not_available = mfs[~mfs.apply(get_nav_data)]

print("data unavaible at the moment for AMC's :\n", not_available.to_list())




