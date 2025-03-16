#!/usr/bin/env python3
"""
Analyses the complexity of IaC code
"""

import argparse
import json
import os
from collections import defaultdict


def analyse_complexity(tool, input_dir, output_file):
    """
    Analyses code complexity based on structure and metrics
    
    Args:
        tool (str): The IaC tool (terraform, cloudformation, opentofu)
        input_dir (str): Directory containing the IaC code
        output_file (str): Where to save the complexity report
    """
    # Ensure input_dir exists
    if not os.path.exists(input_dir):
        print(f"Warning: Directory {input_dir} not found, creating it")
        os.makedirs(input_dir, exist_ok=True)
    
    # Get basic metrics file
    metrics_file = os.path.join("results", "complexity", f"{tool}_metrics.json")
    basic_metrics = {}
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r') as f:
                basic_metrics = json.load(f)
                print(f"Loaded basic metrics: {basic_metrics}")
        except Exception as e:
            print(f"Error loading metrics file: {str(e)}")
            basic_metrics = {
                "tool": tool,
                "total_files": 0,
                "total_lines": 0,
                "resource_count": 0,
                "module_count": 0
            }
    
    # Try to get tool-specific metrics
    tool_metrics = {}
    if tool in ['terraform', 'opentofu']:
        graph_file = os.path.join("results", "complexity", f"{tool}_graph_metrics.json")
        if os.path.exists(graph_file):
            try:
                with open(graph_file, 'r') as f:
                    tool_metrics = json.load(f)
            except Exception as e:
                print(f"Error loading graph metrics: {str(e)}")
    elif tool == 'cloudformation':
        struct_file = os.path.join("results", "complexity", f"{tool}_structure_metrics.json")
        if os.path.exists(struct_file):
            try:
                with open(struct_file, 'r') as f:
                    tool_metrics = json.load(f)
                    print(f"Loaded structure metrics: {tool_metrics}")
            except Exception as e:
                print(f"Error loading structure metrics: {str(e)}")
    
    # Get resource metrics from the basic metrics file
    resource_count = basic_metrics.get('resource_count', 0)
    module_count = basic_metrics.get('module_count', 0)
    
    # Analyze resource types directly from files - with error handling
    try:
        resource_types = analyse_resource_types(tool, input_dir)
    except Exception as e:
        print(f"Error analyzing resource types: {str(e)}")
        resource_types = {}
    
    # Calculate complexity metrics
    complexity_metrics = {
        "tool": tool,
        "resource_count": resource_count,
        "module_count": module_count,
        "resource_types": dict(resource_types),
        "resource_type_count": len(resource_types),
        "basic_metrics": basic_metrics,
        "tool_specific_metrics": tool_metrics
    }
    
    # Calculate complexity score with error handling
    try:
        complexity_score = calculate_complexity_score(
            resource_count, 
            module_count, 
            len(resource_types),
            tool_metrics.get('complexity_score', 0)
        )
    except Exception as e:
        print(f"Error calculating complexity score: {str(e)}")
        complexity_score = 10.0  # Default score
    
    complexity_metrics["complexity_score"] = complexity_score
    
    # Save the report
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(complexity_metrics, f, indent=2)
    except Exception as e:
        print(f"Error saving complexity report: {str(e)}")
    
    print(f"Complexity analysis completed for {tool}")
    print(f"Resource count: {resource_count}")
    print(f"Module count: {module_count}")
    print(f"Resource type count: {len(resource_types)}")
    print(f"Complexity score: {complexity_score}")
    
    return complexity_metrics


def calculate_complexity_score(resource_count, module_count, resource_type_count, tool_score=0):
    """
    Calculate a complexity score based on resources, modules and structure
    
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
    
    # Incorporate tool-specific complexity score if available
    tool_factor = 1.0
    if tool_score > 0:
        tool_factor = tool_score / 50  # Normalize around 1.0
    
    # Calculate final score
    final_score = base_score * module_factor * diversity_factor * tool_factor
    
    return round(final_score, 2)


def analyse_resource_types(tool, input_dir):
    """Analyse resources directly from IaC files"""
    resource_types = defaultdict(int)
    
    # Check if input_dir exists
    if not os.path.exists(input_dir):
        print(f"Warning: Directory {input_dir} doesn't exist")
        return resource_types
    
    if tool in ["terraform", "opentofu"]:
        # Process Terraform/OpenTofu files
        import glob
        import re
        
        tf_files = glob.glob(os.path.join(input_dir, "**/*.tf"), recursive=True)
        
        if not tf_files:
            print(f"No .tf files found in {input_dir}")
            return resource_types
        
        for file_path in tf_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Count resources
                    resource_matches = re.findall(r'resource\s+"([^"]+)"\s+"[^"]+"', content)
                    for resource_type in resource_matches:
                        resource_types[resource_type] += 1
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
    
    elif tool == "cloudformation":
        # Process CloudFormation templates
        import glob
        import re
        
        # For CloudFormation, check templates directory
        templates_dir = os.path.join(input_dir, "templates")
        if os.path.exists(templates_dir):
            input_dir = templates_dir
            
        cf_files = []
        for ext in [".yml", ".yaml", ".json"]:
            cf_files.extend(glob.glob(os.path.join(input_dir, f"**/*{ext}"), recursive=True))
        
        if not cf_files:
            print(f"No CloudFormation template files found in {input_dir}")
            return resource_types
        
        print(f"Found {len(cf_files)} CloudFormation template files")
        
        for file_path in cf_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Use regex to extract resource types
                    type_matches = re.findall(r'Type: (AWS::[a-zA-Z0-9:]+)', content)
                    for resource_type in type_matches:
                        resource_types[resource_type] += 1
                        print(f"Found resource type: {resource_type}")
                        
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
    
    return resource_types


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse IaC code complexity")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--input-dir", required=True, help="Directory containing IaC code")
    parser.add_argument("--output", required=True, help="Output JSON file for complexity report")
    
    args = parser.parse_args()
    
    analyse_complexity(args.tool, args.input_dir, args.output)