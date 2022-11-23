from __future__ import print_function
import json
import boto3
import pyodbc
import os
from secret import get_secret
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


#-----------------------------------------------------------
# Without this set of code, running Lambda locally
# will not output any logging. Got it from this site.
# https://stackoverflow.com/a/45624044/16490514

root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
logging.basicConfig(format='%(asctime)s %(message)s',level=logging.INFO)

secret_arn = os.getenv("CREDENTIALS_SECRET_ARN")

# sts_client = boto3.client("sts")
account_number = boto3.client("sts").get_caller_identity()["Account"]
bucket_name=f"{account_number}-prod-data-archive"

def handler(event, context):

    message = event['Records'][0]
    logging.info(f"From SNS: {message}")
    
    # Fetch and parse secret.
    result = json.loads(get_secret(in_source_db_secret_arn=secret_arn))
    
    # Parse out the items we need from the secret  
    connect_string = result["connect_string"]
    server = result["host"]
    username = result["username"]
    password = result["password"]
    
    logging.debug(f"message is {message}")
    
    # Grab the file name and bucket name from the event and construct the arn.
    file_name = message["s3"]["object"]["key"]
    bucket_arn = message["s3"]["bucket"]["arn"]
    file_arn = bucket_arn + "/" +  file_name
    
    # This is currently hard coded. Remove this when deploying. 
    # This is the recovery target db.
    dbname = "zAdministration"
    
    # The recovery process must connect to a db that is online. Hard code
    # this to the master db. 
    conn_dbname="master"

    logging.info(f"Recovery target database is {dbname}. File is {file_arn}")

    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+conn_dbname+';ENCRYPT=yes;UID='+username+';PWD='+ password)
    
    # Without autocommit, the rds stored proc call to the restore proc will fail.
    cnxn.autocommit=True
    cursor = cnxn.cursor()  
     
    recovery_command=f"exec msdb.dbo.rds_restore_log @restore_db_name={dbname}, @s3_arn_to_restore_from=\"{file_arn}\", @with_norecovery=1" 
    logging.info(f"recovery command is {recovery_command}") 
    
    cursor.execute(recovery_command)


    row = cursor.fetchone() 
    while row: 
        # print(row[0])
        row = cursor.fetchone()
        print(f"{row}")
    cursor.close()

    # This pulls all messages from mssql, so we can close the cursor gracefully.
    # Not doing this and closing the cursor can abort the restore. 
    # while cursor.nextset():
        # pass 
        # cursor.close()        

    return message
