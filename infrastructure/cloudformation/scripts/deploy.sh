#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
STACK_NAME="three-tier-architecture"
REGION="eu-west-1"
S3_BUCKET="tf-state-3tier-architecture"  # Your existing bucket
S3_PREFIX="cloudformation"  # Folder in the bucket for CloudFormation templates
PACKAGED_TEMPLATE="packaged.yaml"

# Directory structure (relative to where the script is run)
TEMPLATE_DIR="templates"
MAIN_TEMPLATE="main.yml"  # Note: .yml extension, not .yaml
PARAMETERS_FILE="parameters.json"

# Function to upload all templates directly to S3
function upload_templates() {
  echo "Uploading templates to S3..."
  
  # Upload main template
  aws s3 cp $TEMPLATE_DIR/$MAIN_TEMPLATE s3://$S3_BUCKET/$S3_PREFIX/$MAIN_TEMPLATE
  
  # Upload all other templates
  for template in $TEMPLATE_DIR/*.yml; do
    filename=$(basename $template)
    if [ "$filename" != "$MAIN_TEMPLATE" ]; then
      echo "Uploading $filename to S3..."
      aws s3 cp $template s3://$S3_BUCKET/$S3_PREFIX/$filename
    fi
  done
  
  echo "All templates uploaded to S3."
}

# Function to deploy the stack
function deploy_stack() {
  # Print start message
  echo "Starting deployment of $STACK_NAME in $REGION"

  # Validate templates
  echo "Validating CloudFormation templates..."
  for template in $TEMPLATE_DIR/*.yml; do
    echo "Validating $template..."
    # Disable the AWS_PAGER to prevent opening in a pager/editor
    export AWS_PAGER=""
    aws cloudformation validate-template --template-body file://$template --region $REGION
  done

  # Upload all templates to S3
  upload_templates

  # Check if stack exists
  if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION 2>/dev/null; then
    # Update existing stack
    echo "Updating existing stack $STACK_NAME..."
    aws cloudformation deploy \
      --template-file $TEMPLATE_DIR/$MAIN_TEMPLATE \
      --stack-name $STACK_NAME \
      --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
      --region $REGION \
      --no-fail-on-empty-changeset
  else
    # Create new stack
    echo "Creating new stack $STACK_NAME..."
    aws cloudformation deploy \
      --template-file $TEMPLATE_DIR/$MAIN_TEMPLATE \
      --stack-name $STACK_NAME \
      --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
      --region $REGION
  fi

  # Wait for stack operation to complete
  echo "Waiting for stack operation to complete..."
  aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION 2>/dev/null || \
  aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION

  # Get stack outputs
  echo "Deployment completed. Stack outputs:"
  aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs" \
    --output table \
    --region $REGION

  echo "Deployment completed successfully!"
}

# Function to destroy the stack
function destroy_stack() {
  echo "Deleting stack $STACK_NAME in $REGION..."
  aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION
  
  echo "Waiting for stack deletion to complete..."
  aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME --region $REGION
  
  echo "Stack deletion completed successfully!"
}

# Check command-line arguments
if [ "$1" == "destroy" ]; then
  destroy_stack
else
  deploy_stack
fi