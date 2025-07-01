# lambda.py - All three Lambda functions

# ===== LAMBDA FUNCTION 1: serializeImageData =====
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    key = event['s3_key']
    bucket = event['s3_bucket']

    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, '/tmp/image.png')

    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

# ===== LAMBDA FUNCTION 2: classifyImage =====
import json
import boto3
import base64
from sagemaker.predictor import Predictor
from sagemaker.serializers import IdentitySerializer

# Fill this in with the name of your deployed model
ENDPOINT = "image-classification-2024-01-XX-XX-XX-XXX"  # Replace with your actual endpoint name

def lambda_handler(event, context):

    # Decode the image data
    image = base64.b64decode(event['body']['image_data'])

    # Instantiate a Predictor
    predictor = Predictor(endpoint_name=ENDPOINT)

    # For this model the IdentitySerializer needs to be "image/png"
    predictor.serializer = IdentitySerializer("image/png")

    # Make a prediction:
    inferences = predictor.predict(image)

    # We return the data back to the Step Function    
    event['body']["inferences"] = inferences.decode('utf-8')
    return {
        'statusCode': 200,
        'body': event['body']
    }

# ===== LAMBDA FUNCTION 3: filterLowConfidenceInferences =====
import json

THRESHOLD = 0.93

def lambda_handler(event, context):

    # Grab the inferences from the event
    inferences = json.loads(event['body']['inferences'])

    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = max(inferences) >= THRESHOLD

    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        return {
            'statusCode': 200,
            'body': event['body']
        }
    else:
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET")

# ===== INDIVIDUAL LAMBDA FILES FOR DEPLOYMENT =====

# Save each function separately when deploying:

# File 1: serialize_image_data.py
"""
import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    key = event['s3_key']
    bucket = event['s3_bucket']
    s3.download_file(bucket, key, '/tmp/image.png')
    
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())
    
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }
"""

# File 2: classify_image.py  
"""
import json
import boto3
import base64
from sagemaker.predictor import Predictor
from sagemaker.serializers import IdentitySerializer

ENDPOINT = "YOUR_ENDPOINT_NAME_HERE"

def lambda_handler(event, context):
    image = base64.b64decode(event['body']['image_data'])
    predictor = Predictor(endpoint_name=ENDPOINT)
    predictor.serializer = IdentitySerializer("image/png")
    inferences = predictor.predict(image)
    
    event['body']["inferences"] = inferences.decode('utf-8')
    return {
        'statusCode': 200,
        'body': event['body']
    }
"""

# File 3: filter_low_confidence.py
"""
import json

THRESHOLD = 0.93

def lambda_handler(event, context):
    inferences = json.loads(event['body']['inferences'])
    meets_threshold = max(inferences) >= THRESHOLD
    
    if meets_threshold:
        return {
            'statusCode': 200,
            'body': event['body']
        }
    else:
        raise Exception("THRESHOLD_CONFIDENCE_NOT_MET")
"""
