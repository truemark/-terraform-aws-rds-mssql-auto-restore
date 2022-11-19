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

def handler(event, context):
  print("Received event: " + json.dumps(event, indent=2))
  # message = "success"
  message = event['Records'][0]['Sns']['Message']
  print("From SNS: " + message)
  
  result = json.loads(get_secret(in_source_db_secret_arn=secret_arn))
  
  connect_string = result["connect_string"]
  username = result["username"]
  host = result["host"]
  password = result["password"]
  port = result["port"]
  
  print(f"username is {username} for db at {connect_string}")
  
  return message

