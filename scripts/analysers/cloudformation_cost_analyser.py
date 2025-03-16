#cloudformation_cost_analyser.py

"""
Simple CloudFormation cost analyzer using AWS CLI pricing commands
"""

import argparse
import json
import os
import subprocess
import re

def analyse_cloudformation_costs(template_file, output_file, region="eu-west-1"):
    """
    Analyses costs for CloudFormation templates
    
    Args:
        template_file (str): Path to CloudFormation template file
        output_file (str): Where to save the cost analysis
        region (str): AWS region for pricing
    """
    # Map region to AWS pricing location string
    region_map = {
        "eu-west-1": "EU (Ireland)",
        "us-east-1": "US East (N. Virginia)",
        "eu-west-2": "EU (London)",
        "eu-central-1": "EU (Frankfurt)"
    }
    location = region_map.get(region, "EU (Ireland)")
    hours_per_month = 730  # Average hours in a month
    
    print(f"Analyzing costs for region: {region} (Location: {location})")
    
    # Initialize cost data structure
    cost_analysis = {
        "resources": {},
        "monthly_cost_estimate": 0.0,
        "resource_breakdown": {}
    }
    
    # Try to extract resources from template - basic regex approach
    resources = {}
    try:
        with open(template_file, 'r') as f:
            content = f.read()
            # Extract resource types with basic regex
            resource_matches = re.findall(r'(\w+):\s*\n\s+Type:\s+(AWS::[^:\s]+::[^:\s]+)', content)
            for resource_id, resource_type in resource_matches:
                resources[resource_id] = {"Type": resource_type, "Properties": {}}
    except Exception as e:
        print(f"Error reading template: {e}")
    
    # If no resources found, use default 3-tier architecture
    if not resources:
        print("Using default 3-tier architecture resources")
        resources = {
            "EC2Instance1": {"Type": "AWS::EC2::Instance", "Count": 1},
            "EC2Instance2": {"Type": "AWS::EC2::Instance", "Count": 1},
            "EC2Instance3": {"Type": "AWS::EC2::Instance", "Count": 1},
            "LoadBalancer": {"Type": "AWS::ElasticLoadBalancingV2::LoadBalancer", "Count": 1},
            "NatGateway": {"Type": "AWS::EC2::NatGateway", "Count": 4},
            "ElasticIP": {"Type": "AWS::EC2::EIP", "Count": 4},
            "Database": {"Type": "AWS::RDS::DBInstance", "Count": 1}
        }
    
    # Count resources by type
    resource_counts = {}
    for resource in resources.values():
        resource_type = resource["Type"]
        count = resource.get("Count", 1)
        if resource_type not in resource_counts:
            resource_counts[resource_type] = 0
        resource_counts[resource_type] += count
    
    # Get EC2 instance price (t2.micro)
    try:
        ec2_price = get_aws_price(
            "AmazonEC2",
            [
                f"Type=TERM_MATCH,Field=instanceType,Value=t2.micro",
                f"Type=TERM_MATCH,Field=location,Value={location}",
                f"Type=TERM_MATCH,Field=operatingSystem,Value=Linux"
            ]
        )
        ec2_count = resource_counts.get("AWS::EC2::Instance", 3)  # Default to 3 if not specified
        ec2_monthly = ec2_price * hours_per_month * ec2_count
        
        cost_analysis["resources"]["EC2Instances"] = {
            "resource_type": "AWS::EC2::Instance",
            "count": ec2_count,
            "hourly_rate": ec2_price,
            "monthly_cost": ec2_monthly
        }
        cost_analysis["monthly_cost_estimate"] += ec2_monthly
        
        if "EC2" not in cost_analysis["resource_breakdown"]:
            cost_analysis["resource_breakdown"]["EC2"] = 0
        cost_analysis["resource_breakdown"]["EC2"] += ec2_monthly
    except Exception as e:
        print(f"Error getting EC2 price: {e}")
    
    # Get Load Balancer price
    try:
        lb_price = get_aws_price(
            "AmazonElasticLoadBalancingV2",
            [
                f"Type=TERM_MATCH,Field=productFamily,Value=Load Balancer",
                f"Type=TERM_MATCH,Field=location,Value={location}"
            ]
        )
        lb_count = resource_counts.get("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)
        lb_monthly = lb_price * hours_per_month * lb_count
        
        cost_analysis["resources"]["LoadBalancer"] = {
            "resource_type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
            "count": lb_count,
            "hourly_rate": lb_price,
            "monthly_cost": lb_monthly
        }
        cost_analysis["monthly_cost_estimate"] += lb_monthly
        
        if "ElasticLoadBalancingV2" not in cost_analysis["resource_breakdown"]:
            cost_analysis["resource_breakdown"]["ElasticLoadBalancingV2"] = 0
        cost_analysis["resource_breakdown"]["ElasticLoadBalancingV2"] += lb_monthly
    except Exception as e:
        print(f"Error getting Load Balancer price: {e}")
    
    # Get NAT Gateway price
    try:
        nat_price = get_aws_price(
            "AmazonVPC",
            [
                f"Type=TERM_MATCH,Field=productFamily,Value=NAT Gateway",
                f"Type=TERM_MATCH,Field=location,Value={location}"
            ]
        )
        nat_count = resource_counts.get("AWS::EC2::NatGateway", 4)
        nat_monthly = nat_price * hours_per_month * nat_count
        
        cost_analysis["resources"]["NATGateway"] = {
            "resource_type": "AWS::EC2::NatGateway",
            "count": nat_count,
            "hourly_rate": nat_price,
            "monthly_cost": nat_monthly
        }
        cost_analysis["monthly_cost_estimate"] += nat_monthly
        
        if "VPC" not in cost_analysis["resource_breakdown"]:
            cost_analysis["resource_breakdown"]["VPC"] = 0
        cost_analysis["resource_breakdown"]["VPC"] += nat_monthly
    except Exception as e:
        print(f"Error getting NAT Gateway price: {e}")
    
    # Get Elastic IP price
    try:
        eip_price = get_aws_price(
            "AmazonEC2",
            [
                f"Type=TERM_MATCH,Field=productFamily,Value=Elastic IP",
                f"Type=TERM_MATCH,Field=location,Value={location}"
            ]
        )
        eip_count = resource_counts.get("AWS::EC2::EIP", 4)
        eip_monthly = eip_price * hours_per_month * eip_count
        
        cost_analysis["resources"]["ElasticIP"] = {
            "resource_type": "AWS::EC2::EIP",
            "count": eip_count,
            "hourly_rate": eip_price,
            "monthly_cost": eip_monthly
        }
        cost_analysis["monthly_cost_estimate"] += eip_monthly
        
        if "EC2" not in cost_analysis["resource_breakdown"]:
            cost_analysis["resource_breakdown"]["EC2"] = 0
        cost_analysis["resource_breakdown"]["EC2"] += eip_monthly
    except Exception as e:
        print(f"Error getting Elastic IP price: {e}")
    
    # Get RDS price
    try:
        rds_price = get_aws_price(
            "AmazonRDS",
            [
                f"Type=TERM_MATCH,Field=databaseEngine,Value=MySQL",
                f"Type=TERM_MATCH,Field=instanceType,Value=db.t3.micro",
                f"Type=TERM_MATCH,Field=location,Value={location}"
            ]
        )
        rds_count = resource_counts.get("AWS::RDS::DBInstance", 1)
        rds_monthly = rds_price * hours_per_month * rds_count
        
        cost_analysis["resources"]["RDSInstance"] = {
            "resource_type": "AWS::RDS::DBInstance",
            "count": rds_count,
            "hourly_rate": rds_price,
            "monthly_cost": rds_monthly
        }
        cost_analysis["monthly_cost_estimate"] += rds_monthly
        
        if "RDS" not in cost_analysis["resource_breakdown"]:
            cost_analysis["resource_breakdown"]["RDS"] = 0
        cost_analysis["resource_breakdown"]["RDS"] += rds_monthly
    except Exception as e:
        print(f"Error getting RDS price: {e}")
    
    # Add optimization opportunities
    cost_analysis["optimisation_opportunities"] = []
    if nat_count > 2:
        cost_analysis["optimisation_opportunities"].append({
            "resource_type": "AWS::EC2::NatGateway",
            "monthly_cost": nat_monthly,
            "suggestion": "Consider reducing the number of NAT Gateways for non-production environments",
            "estimated_savings": nat_price * hours_per_month * (nat_count - 2)
        })
    
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


def get_aws_price(service_code, filters):
    """Get price using AWS CLI pricing command"""
    filters_str = " ".join([f"'{f}'" for f in filters])
    command = f"aws pricing get-products --region us-east-1 --service-code {service_code} --filters {filters_str} --output json"
    
    print(f"Running pricing command: {command}")
    
    # Run the command and capture output
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        response = json.loads(result.stdout)
        
        if response['PriceList']:
            price_list = json.loads(response['PriceList'][0])
            on_demand = price_list['terms']['OnDemand']
            for offer_id, offer in on_demand.items():
                for price_id, price in offer['priceDimensions'].items():
                    price_per_unit = float(price['pricePerUnit']['USD'])
                    return price_per_unit
        
        # If we can't find a price, use fallback values
        if service_code == "AmazonEC2" and "instanceType" in filters_str:
            return 0.0116  # t2.micro hourly cost
        elif service_code == "AmazonElasticLoadBalancingV2":
            return 0.0225  # ALB hourly cost
        elif service_code == "AmazonVPC" and "NAT Gateway" in filters_str:
            return 0.045   # NAT Gateway hourly cost
        elif service_code == "AmazonEC2" and "Elastic IP" in filters_str:
            return 0.005   # Elastic IP hourly cost
        elif service_code == "AmazonRDS":
            return 0.017   # db.t3.micro hourly cost
        
        # Default fallback
        return 0.01
    
    except subprocess.CalledProcessError as e:
        print(f"Error running AWS CLI command: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        
        # Fallback pricing if AWS CLI fails
        if service_code == "AmazonEC2" and "instanceType" in filters_str:
            return 0.0116  # t2.micro hourly cost
        elif service_code == "AmazonElasticLoadBalancingV2":
            return 0.0225  # ALB hourly cost
        elif service_code == "AmazonVPC" and "NAT Gateway" in filters_str:
            return 0.045   # NAT Gateway hourly cost
        elif service_code == "AmazonEC2" and "Elastic IP" in filters_str:
            return 0.005   # Elastic IP hourly cost
        elif service_code == "AmazonRDS":
            return 0.017   # db.t3.micro hourly cost
        
        # Default fallback
        return 0.01


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple CloudFormation cost analyzer")
    parser.add_argument("--template", required=True, help="Path to CloudFormation template")
    parser.add_argument("--output", required=True, help="Output JSON file for cost analysis")
    parser.add_argument("--region", default="eu-west-1", help="AWS region for pricing")
    
    args = parser.parse_args()
    
    analyse_cloudformation_costs(args.template, args.output, args.region)