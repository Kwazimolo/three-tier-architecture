#!/usr/bin/env python3
"""
Processes and normalizes cost data from different sources
"""

import argparse
import json
import os
import glob


def analyse_costs(tool, cost_data_dir, output_file):
    """
    Processes and normalizes cost data
    
    Args:
        tool (str): The IaC tool (terraform, cloudformation, opentofu)
        cost_data_dir (str): Directory containing cost data
        output_file (str): Where to save the cost report
    """
    cost_report = {
        "tool": tool,
        "monthly_cost": 0.0,
        "resource_breakdown": {},
        "cost_optimization_opportunities": []
    }
    
    # Process based on tool
    if tool in ['terraform', 'opentofu']:
        # Process Infracost data
        infracost_file = os.path.join(cost_data_dir, 'infracost.json')
        if os.path.exists(infracost_file):
            with open(infracost_file, 'r') as f:
                infracost_data = json.load(f)
            
            # Extract monthly cost
            cost_report["monthly_cost"] = infracost_data.get('totalMonthlyCost', 0)
            
            # Extract resource breakdown
            resources = infracost_data.get('projects', [{}])[0].get('breakdown', {}).get('resources', [])
            for resource in resources:
                resource_type = resource.get('resourceType', '')
                monthly_cost = resource.get('monthlyCost', 0)
                
                # Categorize by service
                service = resource_type.split('_')[0]
                if service not in cost_report["resource_breakdown"]:
                    cost_report["resource_breakdown"][service] = 0.0
                
                cost_report["resource_breakdown"][service] += monthly_cost
            
            # Extract optimization opportunities
            cost_report["cost_optimization_opportunities"] = extract_optimization_opportunities(infracost_data)
    
    elif tool == 'cloudformation':
        # Process CloudFormation cost analysis
        cf_cost_file = os.path.join(cost_data_dir, 'cost_analysis.json')
        if os.path.exists(cf_cost_file):
            with open(cf_cost_file, 'r') as f:
                cf_cost_data = json.load(f)
            
            cost_report["monthly_cost"] = cf_cost_data.get('monthly_cost_estimate', 0)
            cost_report["resource_breakdown"] = cf_cost_data.get('resource_breakdown', {})
            
            # Generate optimization opportunities
            cost_report["cost_optimization_opportunities"] = generate_cf_optimizations(cf_cost_data)
    
    # Calculate cost efficiency score
    cost_report["cost_efficiency_score"] = calculate_cost_efficiency(cost_report)
    
    # Save the report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(cost_report, f, indent=2)
    
    print(f"Cost analysis completed for {tool}")
    print(f"Estimated monthly cost: ${cost_report['monthly_cost']:.2f}")
    print(f"Cost efficiency score: {cost_report['cost_efficiency_score']}")
    
    return cost_report


def extract_optimization_opportunities(infracost_data):
    """Extract cost optimization opportunities from Infracost data"""
    opportunities = []
    
    # Check for overprovisioned resources
    resources = infracost_data.get('projects', [{}])[0].get('breakdown', {}).get('resources', [])
    
    for resource in resources:
        resource_type = resource.get('resourceType', '')
        monthly_cost = resource.get('monthlyCost', 0)
        
        # Check for expensive EC2 instances
        if 'aws_instance' in resource_type and monthly_cost > 50:
            opportunities.append({
                "resource_type": resource_type,
                "monthly_cost": monthly_cost,
                "suggestion": "Consider using a smaller instance type or Spot Instances",
                "estimated_savings": monthly_cost * 0.7  # Assumption: 70% savings possible
            })
        
        # Check for RDS instances
        elif 'aws_db_instance' in resource_type and monthly_cost > 50:
            opportunities.append({
                "resource_type": resource_type,
                "monthly_cost": monthly_cost,
                "suggestion": "Consider using multi-AZ only in production or using Aurora Serverless",
                "estimated_savings": monthly_cost * 0.4  # Assumption: 40% savings possible
            })
    
    return opportunities


def generate_cf_optimizations(cf_cost_data):
    """Generate optimization opportunities for CloudFormation resources"""
    opportunities = []
    
    for resource_id, resource_data in cf_cost_data.get('resources', {}).items():
        resource_type = resource_data.get('resource_type', '')
        monthly_cost = resource_data.get('monthly_cost', 0)
        
        # Similar logic to extract_optimization_opportunities
        if 'EC2::Instance' in resource_type and monthly_cost > 50:
            opportunities.append({
                "resource_type": resource_type,
                "monthly_cost": monthly_cost,
                "suggestion": "Consider using a smaller instance type or Spot Instances",
                "estimated_savings": monthly_cost * 0.7
            })
    
    return opportunities


def calculate_cost_efficiency(cost_report):
    """
    Calculate a cost efficiency score
    
    Returns a score from 0-100, where 100 is most cost-efficient
    """
    # Base score starts at 80
    base_score = 80
    
    # Adjust for total cost (lower is better)
    monthly_cost = cost_report["monthly_cost"]
    if monthly_cost < 50:
        base_score += 15
    elif monthly_cost < 100:
        base_score += 10
    elif monthly_cost < 200:
        base_score += 5
    elif monthly_cost > 500:
        base_score -= 10
    
    # Adjust for optimization opportunities (more is better)
    opportunity_savings = sum(opp.get("estimated_savings", 0) for opp in cost_report["cost_optimization_opportunities"])
    opportunity_ratio = opportunity_savings / monthly_cost if monthly_cost > 0 else 0
    
    # If high optimization potential, lower the score
    if opportunity_ratio > 0.5:
        base_score -= 15
    elif opportunity_ratio > 0.3:
        base_score -= 10
    elif opportunity_ratio > 0.1:
        base_score -= 5
    
    # Ensure score is within 0-100
    return max(0, min(100, round(base_score, 2)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process and normalize cost data")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--cost-data", required=True, help="Directory containing cost data")
    parser.add_argument("--output", required=True, help="Output JSON file for cost report")
    
    args = parser.parse_args()
    
    analyse_costs(args.tool, args.cost_data, args.output)