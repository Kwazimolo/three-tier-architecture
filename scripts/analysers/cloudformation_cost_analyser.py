#cloudformation_cost_analyser.py

"""
Analyses cost for CloudFormation templates using AWS Price List API
"""

import argparse
import json
import os
import boto3
import yaml

# Simple in-memory cache for pricing API calls
PRICING_CACHE = {}

# Custom YAML constructor for CloudFormation tags
def create_cfn_yaml_constructor():
    # Define custom tag handlers
    def generic_tag_handler(loader, tag_suffix, node):
        # Just return a placeholder tag dictionary
        if isinstance(node, yaml.ScalarNode):
            return {"Ref": node.value} if tag_suffix == "Ref" else {f"{tag_suffix}": node.value}
        elif isinstance(node, yaml.SequenceNode):
            return {"Ref": loader.construct_sequence(node)} if tag_suffix == "Ref" else {f"{tag_suffix}": loader.construct_sequence(node)}
        elif isinstance(node, yaml.MappingNode):
            return {"Ref": loader.construct_mapping(node)} if tag_suffix == "Ref" else {f"{tag_suffix}": loader.construct_mapping(node)}
        return None

    # Create a new SafeLoader with CloudFormation tag handling
    class CloudFormationLoader(yaml.SafeLoader):
        pass

    # Register a handler for each CloudFormation tag
    cfn_tags = ['Ref', 'GetAtt', 'Join', 'Sub', 'Select', 'FindInMap', 'ImportValue', 'Split', 'Transform', 'Cidr', 'Base64']
    for tag in cfn_tags:
        CloudFormationLoader.add_constructor(f"!{tag}", lambda loader, node, tag=tag: generic_tag_handler(loader, tag, node))
        CloudFormationLoader.add_multi_constructor("!", lambda loader, tag_suffix, node: generic_tag_handler(loader, tag_suffix, node))

    return CloudFormationLoader

def analyse_cloudformation_costs(template_file, output_file, region="eu-west-1"):
    """
    Analyses costs for CloudFormation templates
    
    Args:
        template_file (str): Path to CloudFormation template file
        output_file (str): Where to save the cost analysis
        region (str): AWS region for pricing
    """
    # Load the CloudFormation template
    try:
        with open(template_file, 'r') as f:
            if template_file.endswith('.yaml') or template_file.endswith('.yml'):
                # Use custom loader for CloudFormation YAML
                CloudFormationLoader = create_cfn_yaml_constructor()
                template = yaml.load(f, Loader=CloudFormationLoader)
            else:
                template = json.load(f)
    except Exception as e:
        print(f"Error loading template: {e}")
        # Try alternate loading strategy as fallback
        try:
            with open(template_file, 'r') as f:
                # Try to load as plain text and use simple parser
                content = f.read()
                # Basic resource extraction (simplified)
                template = {"Resources": {}}
                
                # Simplistic parsing to extract resource types
                import re
                resource_matches = re.findall(r'Type:\s*([A-Za-z0-9:]+)', content)
                for i, resource_type in enumerate(resource_matches):
                    template["Resources"][f"Resource{i}"] = {"Type": resource_type}
        except Exception as e2:
            print(f"Fallback loading also failed: {e2}")
            template = {"Resources": {}}
    
    # Extract resources
    resources = template.get('Resources', {})
    
    # Initialize AWS pricing client
    pricing_client = boto3.client('pricing', region_name='us-east-1')  # Pricing API only available in us-east-1
    
    # Analyse costs for each resource
    cost_analysis = {
        "resources": {},
        "monthly_cost_estimate": 0.0,
        "resource_breakdown": {}
    }
    
    # Region mapping for AWS Price List API
    region_map = {
        "eu-west-1": "EU (Ireland)",
        "us-east-1": "US East (N. Virginia)",
        # Add more as needed
    }
    location = region_map.get(region, "EU (Ireland)")
    
    for resource_id, resource_data in resources.items():
        resource_type = resource_data.get('Type', '')
        resource_properties = resource_data.get('Properties', {})
        
        # Estimate cost for this resource
        monthly_cost = 0.0
        
        # EC2 instances
        if resource_type == 'AWS::EC2::Instance':
            instance_type = resource_properties.get('InstanceType', 't2.micro')
            # If instance type is a CloudFormation reference or function, default to t2.micro
            if isinstance(instance_type, dict):
                instance_type = 't2.micro'
            
            # Try to get price from API
            try:
                cache_key = f"EC2_{instance_type}_{location}"
                if cache_key in PRICING_CACHE:
                    monthly_cost = PRICING_CACHE[cache_key]
                else:
                    pricing_response = pricing_client.get_products(
                        ServiceCode='AmazonEC2',
                        Filters=[
                            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'}
                        ],
                        MaxResults=1
                    )
                    
                    if pricing_response['PriceList']:
                        price_list = json.loads(pricing_response['PriceList'][0])
                        on_demand = price_list['terms']['OnDemand']
                        for offer_id, offer in on_demand.items():
                            for price_id, price in offer['priceDimensions'].items():
                                price_per_unit = float(price['pricePerUnit']['USD'])
                                monthly_cost = price_per_unit * 730  # 730 hours per month
                                PRICING_CACHE[cache_key] = monthly_cost
                                break
                            break
            except Exception as e:
                print(f"Error getting EC2 pricing: {e}")
                
            # Fallback pricing if API fails
            if monthly_cost == 0:
                cost_map = {
                    't2.micro': 0.0116,
                    't2.small': 0.023,
                    't2.medium': 0.0464,
                    't3.micro': 0.0104,
                    't3.small': 0.0208,
                    't3.medium': 0.0416,
                    'm5.large': 0.096
                }
                monthly_cost = cost_map.get(instance_type, 0.05) * 730
        
        # RDS instances
        elif resource_type == 'AWS::RDS::DBInstance':
            db_instance_class = resource_properties.get('DBInstanceClass', 'db.t3.micro')
            if isinstance(db_instance_class, dict):
                db_instance_class = 'db.t3.micro'
                
            engine = resource_properties.get('Engine', 'mysql')
            if isinstance(engine, dict):
                engine = 'mysql'
                
            multi_az = resource_properties.get('MultiAZ', False)
            if isinstance(multi_az, dict):
                multi_az = False
            
            # Simple mapping for RDS
            db_cost_map = {
                'db.t3.micro': 0.017,
                'db.t3.small': 0.034,
                'db.t3.medium': 0.068,
                'db.m5.large': 0.155
            }
            
            hourly_rate = db_cost_map.get(db_instance_class, 0.05)
            
            # Multi-AZ doubles the cost
            if multi_az:
                hourly_rate *= 2
                
            monthly_cost = hourly_rate * 730
        
        # Load balancers
        elif resource_type == 'AWS::ElasticLoadBalancingV2::LoadBalancer':
            monthly_cost = 0.0225 * 730  # $0.0225/hour
        
        # S3 buckets
        elif resource_type == 'AWS::S3::Bucket':
            monthly_cost = 0.023 * 100  # Assume 100GB @ $0.023/GB
        
        # DynamoDB
        elif resource_type == 'AWS::DynamoDB::Table':
            read_capacity = resource_properties.get('ProvisionedThroughput', {}).get('ReadCapacityUnits', 5)
            if isinstance(read_capacity, dict):
                read_capacity = 5
                
            write_capacity = resource_properties.get('ProvisionedThroughput', {}).get('WriteCapacityUnits', 5)
            if isinstance(write_capacity, dict):
                write_capacity = 5
                
            monthly_cost = (read_capacity * 0.00065 + write_capacity * 0.00065) * 730 + 10 * 0.25  # RCU + WCU + 10GB storage
        
        # Auto Scaling Groups
        elif resource_type == 'AWS::AutoScaling::AutoScalingGroup':
            min_size = resource_properties.get('MinSize', 1)
            if isinstance(min_size, dict):
                min_size = 1
                
            max_size = resource_properties.get('MaxSize', 1)
            if isinstance(max_size, dict):
                max_size = 1
                
            desired_capacity = resource_properties.get('DesiredCapacity', min_size)
            if isinstance(desired_capacity, dict):
                desired_capacity = min_size
                
            monthly_cost = 0.0416 * 730 * desired_capacity  # Assume t3.medium instances
        
        # Add resource to analysis
        if monthly_cost > 0:
            cost_analysis["resources"][resource_id] = {
                "resource_type": resource_type,
                "monthly_cost": monthly_cost
            }
            
            cost_analysis["monthly_cost_estimate"] += monthly_cost
            
            # Categorise by service
            if "::" in resource_type:
                service = resource_type.split('::')[1]
                if service not in cost_analysis["resource_breakdown"]:
                    cost_analysis["resource_breakdown"][service] = 0.0
                
                cost_analysis["resource_breakdown"][service] += monthly_cost
    
    # Add optimisation opportunities
    cost_analysis["optimisation_opportunities"] = find_optimisations(cost_analysis)
    
    # Save the analysis
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cost_analysis, f, indent=2)
    
    print(f"CloudFormation cost analysis completed")
    print(f"Estimated monthly cost: ${cost_analysis['monthly_cost_estimate']:.2f}")
    print("\nBreakdown by service:")
    for service, cost in sorted(cost_analysis["resource_breakdown"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {service}: ${cost:.2f}")
    
    return cost_analysis


def find_optimisations(cost_analysis):
    """Find potential cost optimisations"""
    opportunities = []
    
    for resource_id, resource_data in cost_analysis.get('resources', {}).items():
        resource_type = resource_data.get('resource_type', '')
        monthly_cost = resource_data.get('monthly_cost', 0)
        
        # EC2 instances
        if 'EC2::Instance' in resource_type and monthly_cost > 50:
            opportunities.append({
                "resource_type": resource_type,
                "monthly_cost": monthly_cost,
                "suggestion": "Consider using a smaller instance type or Spot Instances",
                "estimated_savings": monthly_cost * 0.7
            })
        
        # RDS instances
        elif 'RDS::DBInstance' in resource_type and monthly_cost > 50:
            opportunities.append({
                "resource_type": resource_type,
                "monthly_cost": monthly_cost,
                "suggestion": "Consider using multi-AZ only in production or using Aurora Serverless",
                "estimated_savings": monthly_cost * 0.4
            })
    
    return opportunities


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse CloudFormation template costs")
    parser.add_argument("--template", required=True, help="Path to CloudFormation template")
    parser.add_argument("--output", required=True, help="Output JSON file for cost analysis")
    parser.add_argument("--region", default="eu-west-1", help="AWS region for pricing")
    
    args = parser.parse_args()
    
    analyse_cloudformation_costs(args.template, args.output, args.region)