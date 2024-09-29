import json

def lambda_handler(event, context):
    # Log the received event
    print(json.dumps(event))
    # Return the received event
    return event