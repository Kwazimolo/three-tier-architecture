#!/usr/bin/env python3
"""
analyses cost for CloudFormation templates using AWS Price List API
"""

import argparse
import json
import os
import boto3
import yaml


def analyse_cloudformation_costs(template_file, output_file):
    """
    analyses costs for CloudFormation templates
    
    Args:
        template_file (str): Path to CloudFormation template file
        output_file (str): Where to save the cost analysis
    """
    # Load the CloudFormation template
    with open(template_file, 'r') as f:
        if template_file.endswith('.yaml') or template_file.endswith('.yml'):
            template = yaml.safe_load(f)
        else:
            template = json.load(f)
    
    # Extract resources
    resources = template.get('Resources', {})
    
    # Initialize AWS pricing client
    pricing_client = boto3.client('pricing', region_name='us-east-1')  # Pricing API only available in us-east-1
    
    # analyse costs for each resource
    cost_analysis = {
        "resources": {},
        "monthly_cost_estimate": 0.0,
        "resource_breakdown": {}
    }
    
    for resource_id, resource_data in resources.items():
        resource_type = resource_data.get('Type', '')
        resource_properties = resource_data.get('Properties', {})
        
        # Estimate cost for this resource
        resource_cost = estimate_resource_cost(
            pricing_client,
            resource_type,
            resource_properties
        )
        
        if resource_cost:
            cost_analysis["resources"][resource_id] = resource_cost
            cost_analysis["monthly_cost_estimate"] += resource_cost["monthly_cost"]
            
            # Add to resource type breakdown
            resource_category = resource_type.split('::')[1]
            if resource_category not in cost_analysis["resource_breakdown"]:
                cost_analysis["resource_breakdown"][resource_category] = 0.0
            
            cost_analysis["resource_breakdown"][resource_category] += resource_cost["monthly_cost"]
    
    # Save the analysis
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cost_analysis, f, indent=2)
    
    print(f"CloudFormation cost analysis completed")
    print(f"Estimated monthly cost: ${cost_analysis['monthly_cost_estimate']:.2f}")
    
    return cost_analysis


def estimate_resource_cost(pricing_client, resource_type, properties):
    """
    Estimate the cost for a specific CloudFormation resource
    
    This is a simplified version - in a real implementation, you would have
    more detailed mappings and calculations for each AWS resource type
    """
    cost_estimate = {
        "resource_type": resource_type,
        "monthly_cost": 0.0,
        "pricing_factors": {}
    }
    
    # Handle EC2 instances
    if resource_type == 'AWS::EC2::Instance':
        instance_type = properties.get('InstanceType', 't2.micro')
        cost_estimate["pricing_factors"]["instance_type"] = instance_type
        
        # Get EC2 pricing
        try:
            pricing_response = pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'US East (N. Virginia)'},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'}
                ],
                MaxResults=1
            )
            
            if pricing_response['PriceList']:
                price_list = json.loads(pricing_response['PriceList'][0])
                on_demand = price_list['terms']['OnDemand']
                for offer_id, offer in on_demand.items():
                    for price_id, price in offer['priceDimensions'].items():
                        price_per_unit = float(price['pricePerUnit']['USD'])
                        cost_estimate["monthly_cost"] = price_per_unit * 730  # 730 hours per month
                        break
                    break
        except Exception as e:
            print(f"Error getting EC2 pricing: {e}")
            # Use approximate pricing if API fails
            cost_map = {
                't2.micro': 0.0116,
                't2.small': 0.023,
                't2.medium': 0.0464,
                'm5.large': 0.096,
                # Add more as needed
            }
            hourly_rate = cost_map.get(instance_type, 0.05)  # Default if not found
            cost_estimate["monthly_cost"] = hourly_rate * 730
    
    # Handle S3 buckets (very simplified)
    elif resource_type == 'AWS::S3::Bucket':
        # Assume standard storage at $0.023 per GB with 100GB default
        cost_estimate["pricing_factors"]["storage_class"] = "Standard"
        cost_estimate["pricing_factors"]["estimated_size_gb"] = 100
        cost_estimate["monthly_cost"] = 0.023 * 100
    
    # Handle RDS instances
    elif resource_type == 'AWS::RDS::DBInstance':
        db_instance_class = properties.get('DBInstanceClass', 'db.t3.micro')
        engine = properties.get('Engine', 'mysql')
        cost_estimate["pricing_factors"]["db_instance_class"] = db_instance_class
        cost_estimate["pricing_factors"]["engine"] = engine
        
        # Simple mapping (would use API in production)
        db_cost_map = {
            'db.t3.micro': 0.017,
            'db.t3.small': 0.034,
            'db.t3.medium': 0.068,
            # Add more as needed
        }
        
        hourly_rate = db_cost_map.get(db_instance_class, 0.05)  # Default if not found
        cost_estimate["monthly_cost"] = hourly_rate * 730
    
    # Add more resource types as needed
    
    return cost_estimate


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="analyse CloudFormation template costs")
    parser.add_argument("--template", required=True, help="Path to CloudFormation template")
    parser.add_argument("--output", required=True, help="Output JSON file for cost analysis")
    
    args = parser.parse_args()
    
    analyse_cloudformation_costs(args.template, args.output)