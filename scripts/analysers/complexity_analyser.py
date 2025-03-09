#!/usr/bin/env python3
"""
analyses the complexity of IaC code
"""

import argparse
import json
import os


def analyse_complexity(tool, checkov_results_file, output_file):
    """
    analyses code complexity based on Checkov results
    
    Args:
        tool (str): The IaC tool (terraform, cloudformation, opentofu)
        checkov_results_file (str): Path to Checkov results JSON
        output_file (str): Where to save the complexity report
    """
    # Load Checkov results
    with open(checkov_results_file, 'r') as f:
        checkov_data = json.load(f)
    
    # Extract resource types and counts
    resource_types = {}
    resource_count = 0
    module_count = 0
    
    # Process Checkov results to count resources by type
    if 'results' in checkov_data and 'passed_checks' in checkov_data['results']:
        for check in checkov_data['results']['passed_checks'] + checkov_data['results']['failed_checks']:
            resource_type = check.get('resource', '').split('.')[0]
            if resource_type:
                resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
                resource_count += 1
                if resource_type == 'module':
                    module_count += 1
    
    # Calculate complexity metrics
    complexity_metrics = {
        "tool": tool,
        "resource_count": resource_count,
        "module_count": module_count,
        "resource_types": resource_types,
        "resource_type_count": len(resource_types),
        "complexity_score": calculate_complexity_score(resource_count, module_count, len(resource_types)),
        "raw_checkov_findings": {
            "passed": len(checkov_data['results'].get('passed_checks', [])),
            "failed": len(checkov_data['results'].get('failed_checks', [])),
        }
    }
    
    # Save the report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(complexity_metrics, f, indent=2)
    
    print(f"Complexity analysis completed for {tool}")
    print(f"Resource count: {resource_count}")
    print(f"Module count: {module_count}")
    print(f"Resource type count: {len(resource_types)}")
    print(f"Complexity score: {complexity_metrics['complexity_score']}")
    
    return complexity_metrics


def calculate_complexity_score(resource_count, module_count, resource_type_count):
    """
    Calculate a complexity score based on resources and modules
    
    Higher scores indicate more complex infrastructure
    """
    # Base score from resource count (logarithmic to prevent large infrastructures from scoring too high)
    base_score = 10 * (1 + (resource_count / 20))
    
    # Module usage can reduce complexity (reusability), but very high module count increases complexity
    module_factor = 1.0
    if module_count > 0:
        module_factor = 0.9 if module_count < 5 else 1.1
    
    # Resource type diversity increases complexity
    diversity_factor = 1.0 + (resource_type_count / 20)
    
    return round(base_score * module_factor * diversity_factor, 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="analyse IaC code complexity")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--checkov-results", required=True, help="Path to Checkov results JSON")
    parser.add_argument("--output", required=True, help="Output JSON file for complexity report")
    
    args = parser.parse_args()
    
    analyse_complexity(args.tool, args.checkov_results, args.output)