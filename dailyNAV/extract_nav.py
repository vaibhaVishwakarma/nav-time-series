import pandas as pd
import re

def clean_fund_name(fund_name):
    # Use regex to keep everything before 'fund' (including 'fund') and remove everything after it
    cleaned_name = re.sub(r'\s+fund.*', ' fund', fund_name, flags=re.IGNORECASE)
    return cleaned_name.strip()

def create_ISIN_mapping(df):
        
        """Create a mapping of fund names to ISINs."""
        isin_mapping = {}
        for index, row in df.iterrows():
            fund_name = row['Cleaned Fund Name'].lower()
            isin = row['ISIN']
            if fund_name and isin and row['Growth/Regular Type'] in ["Growth", "Regular"]:
                if "hdfc" in fund_name:
                    print(fund_name)
                isin_mapping[fund_name] = isin
        return isin_mapping


def extract_fund_nav(file_path):
    data = []
    current_amc = ""
    current_scheme_type = ""

    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("Open Ended Schemes"):
                    current_scheme_type = line.split('(')[1].split(')')[0].strip()
                elif ";" not in line and not line.startswith("Scheme Code") and not line.startswith(" ") and not line.startswith("Closed Ended Schemes") and not line.startswith("Exchange Traded Funds") and not line.startswith("Interval Fund Schemes"):
                    current_amc = line
                elif line.startswith("Scheme Code"):
                    continue # Skip header line
                else:
                    parts = line.split(';')
                    if len(parts) >= 6:
                        scheme_code = parts[0]
                        isin_div_payout_growth = parts[1]
                        isin_div_reinvestment = parts[2]
                        scheme_name = parts[3]
                        nav = parts[4]
                        date = parts[5]

                        # Determine ISIN
                        isin = isin_div_payout_growth if isin_div_payout_growth != '-' else isin_div_reinvestment

                        # Determine ISIN Type
                        isin_type = "N/A"
                        if isin_div_payout_growth != '-':
                            isin_type = "Payout/Growth"
                        elif isin_div_reinvestment != '-':
                            isin_type = "Reinvestment"

                        # Determine Growth/Regular Type
                        growth_regular_type = "Other"
                        if "DIRECT" in scheme_name.upper():
                            growth_regular_type = "Direct"
                        elif "GROWTH" in scheme_name.upper():
                            growth_regular_type = "Growth"
                        elif "REGULAR" in scheme_name.upper():
                            growth_regular_type = "Regular"

                        # Cleaned Fund Name
                        cleaned_scheme_name = clean_fund_name(scheme_name)
                        #cleaned_scheme_name = re.sub(r'\s*-\s*(DIRECT|REGULAR|RETAIL)\s*-\s*(IDCW|MONTHLY IDCW|QUARTERLY IDCW|DAILY IDCW|ANNUAL IDCW|GROWTH|INCOME DISTRIBUTION CUM CAPITAL WITHDRAWAL OPTION|IDCW PAYOUT|IDCW REINVESTMENT|PLAN|UNITS|OPTION)\s*', '', cleaned_scheme_name, flags=re.IGNORECASE)
                        #cleaned_scheme_name = re.sub(r'\s*-\s*(Direct|Regular|Retail)\s*Plan\s*-\s*(Growth|IDCW)\s*', '', cleaned_scheme_name, flags=re.IGNORECASE)
                        #cleaned_scheme_name = re.sub(r'\s*-\s*(Direct|Regular|Retail)\s*Plan\s*(Growth|IDCW)\s*Option\s*', '', cleaned_scheme_name, flags=re.IGNORECASE)
                        #cleaned_scheme_name = re.sub(r'\s*-\s*(Direct|Regular|Retail)\s*Plan\s*(Growth|IDCW)\s*', '', cleaned_scheme_name, flags=re.IGNORECASE)
                        #cleaned_scheme_name = re.sub(r'\s*-\s*(Direct|Regular|Retail)\s*\s*(Growth|IDCW)\s*Option\s*', '', cleaned_scheme_name, flags=re.IGNORECASE)
                        #cleaned_scheme_name = re.sub(r'\s*-\s*(Direct|Regular|Retail)\s*\s*(Growth|IDCW)\s*', '', cleaned_scheme_name, flags=re.IGNORECASE)
                        #cleaned_scheme_name = re.sub(r'\s*\(Formerly Known as[^)]+\)', '', cleaned_scheme_name)
                        #cleaned_scheme_name = cleaned_scheme_name.strip()
                        
                        

                        # Filter for "DIRECT" or "Growth" or "REGULAR" funds
                        if growth_regular_type in ["Direct", "Growth", "Regular"]:
                            data.append({
                                "ISIN": isin,
                                "ISIN Type": isin_type,
                                "Scheme Code": scheme_code,
                                "Scheme Name": scheme_name,
                                "Cleaned Fund Name": cleaned_scheme_name,
                                "Scheme Type": current_scheme_type,
                                "AMC Name": current_amc,
                                "Nav": nav,
                                "Growth/Regular Type": growth_regular_type
                            })

    except Exception as e:
        print(f"Error reading file: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    return df



if __name__ == "__main__":
    file_path = "dailyNAV/NAVAll_2025-06-27.txt"
    df = extract_fund_nav(file_path)
    lookup= create_ISIN_mapping(df)
    fund_name="HDFC Flexi Cap fund"
    print(fund_name.lower())

    if fund_name.lower() in lookup:
        print(f"ISIN for {fund_name.lower()}: {lookup[fund_name.lower()]}")
    else:
        print(f"No ISIN found for {fund_name}")