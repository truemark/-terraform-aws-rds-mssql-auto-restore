from __future__ import print_function
import json
print('Loading function')

def handler(event, context):
  #print("Received event: " + json.dumps(event, indent=2))
  message = event['Records'][0]['Sns']['Message']
  print("From SNS: " + message)
  return message
