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
secret_db_name = secret_arn.split("/")[1]

account_number = boto3.client("sts").get_caller_identity()["Account"]
bucket_name=f"{account_number}-prod-data-archive"

# The recovery process must connect to a db that is online. Hard code
# this to the master db. 
conn_dbname="master"

def handler(event, context):

    logging.debug(f"-----------------raw event is {event}")
    logging.info(f"loading json from {event['Records'][0]}")
    message = json.dumps(event)
    logging.info(f"From SNS: {message}")
    
    # Fetch and parse secret.
    result = json.loads(get_secret(in_source_db_secret_arn=secret_arn))
    
    # Parse out the items we need from the secret  
    connect_string = result["connect_string"]
    server = result["host"]
    username = result["username"]
    password = result["password"]
    msg = json.loads(json.loads(message)['Records'][0]['Sns']['Message'])
    file_name = msg['Records'][0]['s3']['object']['key']
    event_db_name = file_name.split("/")[1]
    
    if event_db_name != secret_db_name :
        logging.info(f"db name mismatch between event db and target db: {event_db_name} {secret_db_name}")
        message = f"File {file_name} is not for server {secret_db_name}. Exiting."

    else:
        
        logging.debug(f"{file_name} {event_db_name} {secret_db_name} message is {message}")
        
        # Grab the bucket name from the event and construct the arn.
        bucket_arn = msg['Records'][0]['s3']['bucket']['arn']
        file_arn = bucket_arn + "/" + file_name
        logging.info(f"recovery file arn is {file_arn}")
        
        # Yank the recovery dbname from the file name.
        # recovery_dbname = file_name.split("/")[2]
        # This is currently hard coded. Remove this when deploying. 
        recovery_dbname = "zAdministration"
    
        logging.info(f"Recovery target database is {recovery_dbname}. File is {file_arn}")
    
        cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+conn_dbname+';ENCRYPT=yes;UID='+username+';PWD='+ password)
        
        # Without autocommit, the rds stored proc call to the restore proc will fail.
        cnxn.autocommit=True
        cursor = cnxn.cursor()  
         
        recovery_command=f"exec msdb.dbo.rds_restore_log @restore_db_name={recovery_dbname}, @s3_arn_to_restore_from=\"{file_arn}\", @with_norecovery=1" 
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
        message = f"successfully initiated restore of file {file_arn}"

    return message
