import time
import configparser
import datetime
import subprocess
import logging, logging.config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import warnings
warnings.filterwarnings("ignore")
import sys
import os
import sqlalchemy as sa
import urllib.parse
import pandas as pd
import configparser
import logging
import os
import time
import numpy as np
import pymssql
from sqlalchemy import text,create_engine
import sys
from pathlib import Path
import subprocess


st = time.time()
#dbTable = sys.argv[1]

driver = '{ODBC Driver 17 for SQL Server}'
serverName = 'LAPTOP-82AUC5I5\\SQLEXPRESS' #sys.argv[3];
databaseName = 'app' #sys.argv[4];
destination_table = 'angelone_stock_history' #sys.argv[5];


def establishDBConnection(server = serverName, database = databaseName):
    engine = sa.create_engine(f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes")
    conn = engine.connect()
    if conn:
        #print("Connected successfully!")
        logging.info("connection successfully established with DB")
    return conn


# logging.info(sql)
conn =establishDBConnection()
# conn.execute(text(sql))
# conn.commit()


driver = '{ODBC Driver 17 for SQL Server}'
serverName = 'LAPTOP-82AUC5I5\\SQLEXPRESS' #sys.argv[3];
databaseName = 'APP' #sys.argv[4];
#userId = sys.argv[5];
#password = sys.argv[6];
loop_value_code = "select top 1 id from "+destination_table+" order by id desc"
val = pd.read_sql(loop_value_code,conn)
val = val['id'][0] if not val.empty else 0
logging.info(f"Last ID in destination table: {val}")

csv_path = Path(__file__).parent / "stocks_output.csv"
clean_csv_path = Path(__file__).parent / "stocks_output_clean.csv"

logging.info(f"Reading CSV from {csv_path}")
df = pd.read_csv(csv_path)
for col in ["ltp", "change_value", "change_percent"]:
    df[col] = df[col].astype(str).str.replace(r"[^0-9.\-]", "", regex=True)

df["page_no"] = pd.to_numeric(df["page_no"], errors="coerce").astype("Int64")
df["run_date"] = pd.to_datetime(df["run_date"], errors="coerce").dt.strftime("%Y-%m-%d")

# Match the target table's column order and include the missing id value.
df.insert(0, "id", range(val + 1, val + len(df) + 1))
df.rename(columns={"company": "company_name", "url": "stock_url"}, inplace=True)
df = df[["id", "company_name", "symbol", "ltp", "change_value", "change_percent", "stock_url", "page_no", "run_date"]]

df.to_csv(clean_csv_path, index=False)
logging.info(f"Cleaned CSV written to {clean_csv_path}")

subprocess.run(
    [
        "bcp",
        f"{databaseName}.dbo.{destination_table}",
        "in",
        str(clean_csv_path),
        "-S", serverName,
        "-T",
        "-c",
        "-t", ",",
        "-F", "2"
    ],
    check=True
)


timeElapsed = time.time() - st
logging.info("Data push to SQL completed in "+str(round(timeElapsed,2))+" Seconds")

# Print head of the Data for Validation..
 
validationQuery = """select TOP 10 * from """+destination_table
 
logging.info(validationQuery)
validationData = pd.read_sql(validationQuery,conn)
logging.info(validationData)
conn.close()