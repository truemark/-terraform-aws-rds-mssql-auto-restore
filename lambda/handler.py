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

print('Loading function')

secret_arn = os.getenv("CREDENTIALS_SECRET_ARN")

sts_client = boto3.client("sts")
account_number = sts_client.get_caller_identity()["Account"]
bucket_name=f"{account_number}-prod-data-archive"

def handler(event, context):

    message = event['Records'][0]
    logging.debug(f"From SNS: {message}")
    
    # Fetch and parse secret.
    result = json.loads(get_secret(in_source_db_secret_arn=secret_arn))
      
    connect_string = result["connect_string"]
    username = result["username"]
    server = result["host"]
    password = result["password"]
    # Port not needed, it's in the connect string
    # port = result["port"]
    

    file_arn = "arn:aws:s3:::"+ bucket_name + "/" +  message["s3"]["object"]["key"]
    dbname = "zAdministration"
    conn_dbname="zAdmin2"

    logging.debug(f"username is {username}  {dbname} {file_arn} at {connect_string}")

  
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+conn_dbname+';ENCRYPT=yes;UID='+username+';PWD='+ password)
    
    # Without autocommit, the rds stored proc call to the restore proc will fail.
    cnxn.autocommit=True
    cursor = cnxn.cursor()  
     
    recovery_command=f"exec msdb.dbo.rds_restore_log @restore_db_name={dbname}, @s3_arn_to_restore_from=\"{file_arn}\", @with_norecovery=1" 
    logging.debug(f"recovery command is {recovery_command}") 
    
    cursor.execute(recovery_command)


    row = cursor.fetchone() 
    while row: 
        # print(row[0])
        row = cursor.fetchone()
        print(f"{row}")

    # This pulls all messages from mssql, so we can close the cursor gracefully.
    # Not doing this and closing the cursor can abort the restore. 
    while cursor.nextset():
        # pass 
        # cursor.close()        

    return message
