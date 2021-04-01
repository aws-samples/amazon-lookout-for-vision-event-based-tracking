# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 2020

@author: Michael Wallner (Amazon Web Services)
@email: wallnm@amazon.com
"""

# Import libraries
import os
import json, boto3
import base64, binascii
from botocore.exceptions import ClientError
from datetime import datetime

# Set global variables (found in environemnt vars in Lambda):
# - PROJECT_NAME: Lookout project name to invoke
# - S3_BUCKET: S3 bucket to save images to
# - INSTANCE_ID: Amazon Connect InstaceId
# - FLOW_ID: Contact Flow ID
# - SOURCE_NUMBER: Your claimed Amazon Connect phone number
# - DEST_NUMBER: Your mobile phone number
PROJECT_NAME = os.getenv("PROJECT_NAME")
S3_BUCKET = os.getenv("S3_BUCKET")
INSTANCE_ID = os.getenv("INSTANCE_ID")
FLOW_ID = os.getenv("FLOW_ID")
SOURCE_NUMBER = os.getenv("SOURCE_NUMBER")
DEST_NUMBER = os.getenv("DEST_NUMBER")

# Get boto3 clients:
# - Amazon Lookout for Vision
# - S3
# - Amazon Connect
lookout = boto3.client("lookoutvision")
s3 = boto3.client("s3")
connect = boto3.client("connect")

def lambda_handler(event, context):
    """Main entry function.

    Args:
        event (json): events coming from Amazon Connect
        context (json): context attributes

    Returns:
        output (json): returning success or failure

    Examples:

        >>> output = lambda_handler(event={...}, context={...})

    """
    # Debugging
    print("Event from website:", event)
    # Base64 decode event body
    body = base64.b64decode(event["body"])
    # Read bytes from the image (optional also get coordinates)
    body_bytes = json.loads(body)["image"].split(",")[-1]
    body_bytes = base64.b64decode(body_bytes)
    # coordinates = json.loads(body)["coordinates"].split(",")[-1]
    # Set dttm for image string.
    # Note: You can also go and partition per date(-time)
    now = datetime.now()
    dttm = now.strftime("%Y-%m-%d-%H-%M-%S")
    key = "upload-{}.jpg".format(dttm)
    # Write image to S3
    put = s3.put_object(
        Bucket=S3_BUCKET,
        Key="uploads/{}".format(key),
        Body=body_bytes
    )
    # Check if image is anomalous:
    response = lookout.detect_anomalies(
        ProjectName=PROJECT_NAME,
        ModelVersion='1',
        Body=body_bytes,
        ContentType='image/jpeg'
    )
    # If the image showed an anomaly, then use Amazon Connect to
    # call the DestinationPhoneNumber (your mobile phone number)
    if response["DetectAnomalyResult"]["IsAnomalous"]:
        call = connect.start_outbound_voice_contact(
            DestinationPhoneNumber=DEST_NUMBER,
            ContactFlowId=FLOW_ID,
            InstanceId=INSTANCE_ID,
            SourcePhoneNumber=SOURCE_NUMBER,
            Attributes={
                "Confidence": str(int(response["DetectAnomalyResult"]["Confidence"]*100))
            }
        )
    # Return headers as this is used in an AJAX call:
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": event["headers"]["origin"],
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        "body": json.dumps(response["DetectAnomalyResult"])
    }