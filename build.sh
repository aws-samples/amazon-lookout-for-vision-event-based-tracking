# #!/bin/sh

# Global variables
ApplicationRegion="YOUR_REGION"
S3SourceBucket="YOUR_S3_BUCKET-sagemaker"
LookoutProjectName="YOUR_PROJECT_NAME"
FlowID="YOUR_FLOW_ID"
InstanceID="YOUR_INSTANCE_ID"
SourceNumber="YOUR_CLAIMED_NUMBER"
DestNumber="YOUR_MOBILE_PHONE_NUMBER"
CloudFormationStack="YOUR_CLOUD_FORMATION_STACK_NAME"

## Create S3 bucket and set parameters for CloudFormation stack
# Build your paramater string for the CFT
JSON_PARAM="ParameterKey=S3SourceBucket,ParameterValue=%s ParameterKey=LookoutProjectName,ParameterValue=%s ParameterKey=FlowID,ParameterValue=%s ParameterKey=InstanceID,ParameterValue=%s ParameterKey=SourceNumber,ParameterValue=%s ParameterKey=DestNumber,ParameterValue=%s"
JSON_PARAM=$(printf "$JSON_PARAM" "$S3SourceBucket" "$LookoutProjectName" "$FlowID" "$InstanceID" "$SourceNumber" "$DestNumber")

# Create your S3 bucket
if [ "$ApplicationRegion" = "us-east-1" ]; then
	aws s3api create-bucket --bucket $S3SourceBucket
else
	aws s3api create-bucket --bucket $S3SourceBucket --create-bucket-configuration LocationConstraint=$ApplicationRegion
fi

## Code build and resource upload

# ZIP files for Lambda functions
mkdir resources
echo "ZIP Python files"
files="amazon-lookout-vision-api"
for file in $files
do
    output="../../resources/$file.zip"
    cd lambda-functions/$file
    zip -r $output *.py
    cd ../../
done

# Upload resources to S3
echo "Upload files to S3"
aws s3 cp cloudformation/template.yaml s3://$S3SourceBucket
files="amazon-lookout-vision-api"
for file in $files
do
    input="resources/$file.zip"
    aws s3 cp $input s3://$S3SourceBucket
done
rm -rf resources

## Run CFT stack creation
aws cloudformation create-stack --stack-name $CloudFormationStack --template-url https://$S3SourceBucket.s3.$ApplicationRegion.amazonaws.com/template.yaml --parameters $JSON_PARAM --capabilities CAPABILITY_NAMED_IAM
