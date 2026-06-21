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

st = time.time()
#dbTable = sys.argv[1]

destination_table='BCP_test'
driver = '{ODBC Driver 17 for SQL Server}'
serverName = 'LAPTOP-82AUC5I5\\SQLEXPRESS' #sys.argv[3];
databaseName = 'vscode' #sys.argv[4];
destination_table = 'angelone_stock_history' #sys.argv[5];

# Establishing Connection to the Database
# def establishDBConnection():
#     #logging.info('Establishing connection to the Database ..')
   
#     conn = pymssql.connect(serverName,databaseName)
    
#     if conn:
#         #print ("Connection successfully established with DB ...")
#         logging.info("connection successfully established with DB")
       
#     return conn

def establishDBConnection(server = serverName, database = databaseName):
    engine = sa.create_engine(f"mssql+pyodbc://@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes")
    conn = engine.connect()
    if conn:
        #print("Connected successfully!")
        logging.info("connection successfully established with DB")
    return conn
    


# Absolute path of the Root Folder
#basepath = os.path.dirname(os.path.dirname(os.path.abspath('__file__'))) 

# sql="""IF OBJECT_ID('"""+destination_table+"""', 'U') IS NOT NULL 
#   DROP TABLE """+destination_table+""";
  
#   CREATE TABLE """+destination_table+""" (
#     site_id varchar(100),
#     account_id varchar(60),
#     rclv float,
#     segment varchar(60),
#     run_date date
#   );

# """


# logging.info(sql)
conn =establishDBConnection()
# conn.execute(text(sql))
# conn.commit()


driver = '{ODBC Driver 17 for SQL Server}'
serverName = 'LAPTOP-82AUC5I5\\SQLEXPRESS' #sys.argv[3];
databaseName = 'APP' #sys.argv[4];
#userId = sys.argv[5];
#password = sys.argv[6];

# try:
#     subprocess.run(["bash","executeBCP.bash",databaseName+'.'+destination_table+" in rclvResults.csv",serverName],check=True, universal_newlines=True)
 
# except Exception as e:
#     raise RuntimeError('BCP Command Failed. Customer Predictions have been written to the CSV already, try executing BCP Command from terminal directly..')

from pathlib import Path
import subprocess

csv_path = Path(__file__).parent / "stocks_output.csv"

subprocess.run(
    [
        "bcp",
        f"{databaseName}.dbo.{destination_table}",
        "in",
        str(csv_path),
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