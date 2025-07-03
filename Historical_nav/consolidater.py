import os 
import pandas as pd
import numpy as np

def consolidater(directory_path = "./", output_nav_file_path= "nav_time_series.csv"):
    text_files = list(filter( lambda x : x.endswith(".txt"), os.listdir(directory_path)))

    total_df = pd.DataFrame()
    for file in text_files:
        df = pd.read_csv(os.path.join(directory_path , file) ,delimiter=";" )
        df = df[df["Scheme Code"].fillna("-").astype(str).apply(lambda x : x.isdigit())]

        df["Scheme Code"] = df["Scheme Code"].astype(int)
        df["Net Asset Value"] =df["Net Asset Value"].replace("N.A." ,np.nan)
        df["Date"] = pd.to_datetime(df['Date'], errors = "coerce").dt.strftime('%Y-%m-%d')
        df.dropna(subset=['Date',"Net Asset Value"], inplace=True)
        df["Net Asset Value"] =df["Net Asset Value"].astype(np.float64)

        df = df.drop(["Sale Price" , "Repurchase Price"] , axis = 1)
        total_df = pd.concat([total_df, df])
    total_df.to_csv(output_nav_file_path, index=False, sep=";")

    return total_df

if __name__ == "__main__":
    
    directory_path =  "Historical_nav/"
    output_nav_file_path = "Historical_nav/nav_time_series.csv"
    total_df = consolidater(directory_path , output_nav_file_path)
    print(total_df.iloc[:100])