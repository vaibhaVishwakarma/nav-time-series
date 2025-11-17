import pandas as pd
import requests
import os
import re


class HistoricalNAVDownloader:
    def __init__(self, path_BSESchemeData = r"core\SchemeData090825.csv",
                     path_output_folder = "historical_nav",
                     years_back = 10):
        
        # Handle exceptions
        # Assign class attributes
        self.path_BSESchemeData = path_BSESchemeData
        self.path_output_folder= path_output_folder,
        self.years_back = years_back

        if(not os.path.exists(path_BSESchemeData)):
            print("Please provide a valid path for BSE Scheme Data sheet")
            raise FileNotFoundError("BSE Scheme Data file not found")
        os.makedirs(path_output_folder, exist_ok=True)

        try:

            self.BSESchemeData = self._read_excel(path_BSESchemeData).astype(str)
            # Filter required Fields
            self.amfi_code_col = "Code"
            self.scheme_name_col = "Scheme NAV Name"
            self.payout_ISIN_col = "ISIN Div Payout/ ISIN Growth"
            self.reinvest_ISIN_col = "ISIN Div Reinvestment"
            self.BSESchemeData = self.BSESchemeData[["Code", "Scheme NAV Name","ISIN Div Payout/ ISIN GrowthISIN Div Reinvestment"]].astype(str)
            # Segeragate / Refine ISIN Columns 
            for idx , row in self.BSESchemeData.iterrows():
                matches = self._get_isin(row["ISIN Div Payout/ ISIN GrowthISIN Div Reinvestment"])
                self.BSESchemeData.at[idx, self.payout_ISIN_col] = matches[0]
                self.BSESchemeData.at[idx, self.reinvest_ISIN_col] = matches[1]
    
            self.dates = self._get_dates()

        except Exception as e:
            print(f"Error Initialising HistoricalNAVDownloader {str(e)}")


        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "www.amfiindia.com",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1"
        }

    

    # -- main methods --
    def get_all_from_scheme_data(self):
        self._fetch_store(self.BSESchemeData)

    def get_nav_history(self, list_amfi_codes = [], list_ISINs = []):
        list_amfi_codes = list(map(str, list_amfi_codes))

        def process_row(row):
            code = row[self.amfi_code_col]
            payout = row[self.payout_ISIN_col]
            reinvest = row[self.reinvest_ISIN_col]

            if(code in list_amfi_codes or
                payout in list_ISINs or
                reinvest in list_ISINs):
                return True

            return False
        
        self.filtered_indices = self.BSESchemeData[self.BSESchemeData.apply(process_row, axis = 1)]
        self._fetch_store(self.filtered_indices)


    def _fetch_store(self, df:pd.DataFrame):
        for idx,row in df.iterrows():
            try:
                code = row.get(self.amfi_code_col,"")
                name = row.get(self.scheme_name_col,"")
                paygrow = row.get(self.payout_ISIN_col,"")
                reinvest = row.get(self.reinvest_ISIN_col,"")
                sale_price=""
                header = "Scheme Code;Scheme Name;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Net Asset Value;Repurchase Price;Sale Price;Date"
                text = ""
                
                data_points = self._get_data_points(code)
                
                if len(data_points) == 0:
                    print(f"Skipped {name} - AMFI code: {code} | payout/grow ISIN: {paygrow} | reinvest ISIN: {reinvest} \nNo data available from {self.dates[-1].strftime("%d-%b-%Y")} to {self.dates[0].strftime("%d-%b-%Y")}")
                    continue 

                for record in data_points:
                    date = record.get("date","")
                    date = pd.Timestamp(date).strftime("%d-%b-%Y")
                    nav = record.get("nav","")
                    repurchase = record.get("repurchase","")
                    new_record = [code, name, paygrow, reinvest, nav, repurchase, sale_price, date]
                    filter  = lambda x: "" if not x or pd.isna(x) else str(x)
                    new_record = list(map(filter, new_record))
                    new_line = ";".join(new_record)
                    text+= "\n" + new_line
                filename = f"{name}.txt"
                if(isinstance(self.path_output_folder,tuple)):
                    self.path_output_folder = self.path_output_folder[0]
                filepath = os.path.join(self.path_output_folder, filename)

                text = header + "\n" + text
                with open(filepath, "w") as f:
                    f.write(text) 
                print(f"Processed {name} - AMFI code: {code} | payout/grow ISIN: {paygrow} | reinvest ISIN: {reinvest} \nfrom {self.dates[-1].strftime("%d-%b-%Y")} to {self.dates[0].strftime("%d-%b-%Y")}")
            except Exception as e:
                print(f"Error {name} - AMFI code: {code} | payout/grow ISIN: {paygrow} | reinvest ISIN: {reinvest}\n{str(e)} - {e.__traceback__.tb_lineno}")

    def _get_data_points(self, amfi_code):
        data_points = []
        from_date = self.dates[-1]

        for to_date in self.dates[::-1][1:] :
            url = self._build_url(from_Date= from_date, to_Date= to_date, amfi_code=amfi_code)
            resp = requests.get(url, headers=self.headers, timeout=30)

            if not resp.ok:
                print(f"No response [{resp.status_code}]\n{url}")
                from_date = to_date
                continue
            data = resp.json()

            try:
                points = data["data"]["nav_groups"][0]["historical_records"]
                data_points.extend(points)
                print(len(data_points))

            except Exception as e:
                print(f"Error Fetching data Code: {amfi_code} \nfrom {from_date.strftime("%d-%b-%Y")} to {to_date.strftime("%d-%b-%Y")}\n{url}\n{str(e)}")

            from_date = to_date
        return data_points



    # -- util methods --    
    # Generate URL for json Data of provided Scheme on the given time period
    def _build_url(self,from_Date:pd.Timestamp ,to_Date:pd.Timestamp ,amfi_code):
        return f"https://www.amfiindia.com/api/nav-history?query_type=historical_period&from_date={from_Date.strftime("%Y-%m-%d")}&to_date={to_Date.strftime("%Y-%m-%d")}&sd_id={amfi_code}"

    def _get_dates(self):
        """
    
        """

        yrs = self.years_back
        dates: pd.Timestamp= [pd.Timestamp.today()]
        while(yrs>=5):
            dates.append(dates[-1] - pd.Timedelta(days=365*5 - 7))
            yrs -= 5
        if(yrs>0):
            dates.append(dates[-1] - pd.Timedelta(days= 365*yrs))
        return dates

    def _get_isin(self,string):
        if not isinstance(string, str):
            return [None, None]
        isin_pattern = "[A-Z]{3}[0-9A-Z]{9}"
        matches =  re.findall(isin_pattern, string)
        if(len(matches)) == 0: return [None, None]
        if(len(matches) == 1): matches.append(None)
        return matches


    # --- last function  ---
    def _read_excel(self, file_path):
        file_ext = str(file_path).lower()
        rt = None

        try:
            if file_ext.endswith(".xlsb"):
                rt= pd.read_excel(file_path, engine="pyxlsb")

            elif file_ext.endswith(".xls") or  file_ext.endswith(".xlsx") or file_ext.endswith(".xlsm"):
                rt= pd.read_excel(file_path)

            elif file_ext.endswith(".csv"):
                rt= pd.read_csv(file_path)
           
            else:
                print(f"Unsupported File Extention: {file_path}\nReason: {str(e)}")
                return None
            
            return rt
  
        except Exception as e:
            print(f"Error reading file: {file_path}\nReason: {str(e)}")
            return None
    

if __name__ == "__main__":
    downloader = HistoricalNAVDownloader(path_output_folder="historical_nav_test")
    print(downloader.dates)
    downloader.get_nav_history(list_amfi_codes=["100119"], list_ISINs=["INF209K011W7"])

