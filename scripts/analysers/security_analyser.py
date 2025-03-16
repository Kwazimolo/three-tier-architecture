#!/usr/bin/env python3
"""
Analyses security findings from Checkov for IaC code
"""

import argparse
import json
import os
import sys


def safe_load_json(file_path):
    """
    Safely load JSON file with error handling
    
    Args:
        file_path (str): Path to JSON file
    
    Returns:
        dict: Parsed JSON or empty dictionary
    """
    try:
        with open(file_path, 'r') as f:
            # Read entire file and trim any trailing garbage
            content = f.read()
            
            # Clean the JSON content, removing any characters after the closing brace
            cleaned_content = content.split('}')[0] + '}'
            
            # If the content is empty or doesn't look like valid JSON, return an empty dict
            if not cleaned_content.strip():
                print(f"Empty or invalid content in {file_path}")
                return {}
            
            data = json.loads(cleaned_content)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        # If all else fails, try to parse the last valid JSON
        try:
            # Attempt to find the last valid JSON object
            last_brace = content.rfind('}')
            if last_brace != -1:
                valid_json = content[:last_brace+1]
                data = json.loads(valid_json)
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
        return {}


def extract_detailed_failures(failed_checks):
    """
    Extract and categorise detailed failure information
    
    Args:
        failed_checks (list): List of failed checks from Checkov
    
    Returns:
        dict: Categorised and summarised failure information
    """
    # Categorise failures
    failure_categories = {}
    failure_details = []
    
    for check in failed_checks:
        # Extract key information about the failure
        failure_info = {
            "check_id": check.get('check_id', 'Unknown'),
            "bc_check_id": check.get('bc_check_id', 'N/A'),
            "check_name": check.get('check_name', 'Unnamed Check'),
            "resource": check.get('resource', 'Unknown Resource'),
            "severity": check.get('severity', 'Unknown'),
            "guideline": check.get('guideline', 'No additional guideline')
        }
        
        # Categorise by check name or resource type
        category_key = check.get('check_name', 'Miscellaneous').split()[0]
        if category_key not in failure_categories:
            failure_categories[category_key] = 0
        failure_categories[category_key] += 1
        
        failure_details.append(failure_info)
    
    # Sort failures by frequency of category
    sorted_categories = sorted(
        failure_categories.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    return {
        "total_failures": len(failed_checks),
        "failure_categories": dict(sorted_categories),
        "detailed_failures": failure_details[:50]  # Limit to top 50 for readability
    }


def analyse_security(tool, check_file, output_file):
    """
    Analyses security findings from Checkov
    
    Args:
        tool (str): The IaC tool (terraform, cloudformation, opentofu)
        check_file (str): Path to combined Checkov check results
        output_file (str): Where to save the security report
    """
    # Load check results
    checkov_data = safe_load_json(check_file)
    
    # Extract summary information
    summary = checkov_data.get('summary', {})
    results = checkov_data.get('results', {})
    
    # Extract failed checks
    failed_checks = results.get('failed_checks', [])
    
    # Total checks calculation
    total_checks = summary.get('passed', 0) + summary.get('failed', 0)
    pass_percentage = round(100 * summary.get('passed', 0) / total_checks, 2) if total_checks > 0 else 0
    
    # Extract detailed failure information
    failure_analysis = extract_detailed_failures(failed_checks)
    
    # Prepare security metrics
    security_metrics = {
        "tool": tool,
        "summary": {
            "total_checks": total_checks,
            "passed_checks": summary.get('passed', 0),
            "failed_checks": summary.get('failed', 0),
            "skipped_checks": summary.get('skipped', 0),
            "parsing_errors": summary.get('parsing_errors', 0),
            "resource_count": summary.get('resource_count', 0),
            "checkov_version": summary.get('checkov_version', 'Unknown')
        },
        "security_assessment": {
            "pass_percentage": pass_percentage,
            "security_score": pass_percentage,
            "total_resources": summary.get('resource_count', 0)
        },
        "failure_analysis": failure_analysis
    }
    
    # Save the report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(security_metrics, f, indent=2)
    
    # Logging
    print(f"Security analysis completed for {tool}")
    print(f"Total checks: {total_checks}")
    print(f"Passed checks: {summary.get('passed', 0)}")
    print(f"Failed checks: {summary.get('failed', 0)}")
    print(f"Pass percentage: {pass_percentage:.2f}%")
    print("\nFailure Categories:")
    for category, count in failure_analysis['failure_categories'].items():
        print(f"- {category}: {count}")
    
    return security_metrics


def validate_report(report_file):
    """
    Validate the security report
    
    Args:
        report_file (str): Path to the security report
    
    Returns:
        bool: True if report is valid, False otherwise
    """
    try:
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        # Basic validation checks
        required_keys = ['tool', 'summary', 'security_assessment', 'failure_analysis']
        for key in required_keys:
            if key not in report:
                print(f"Missing required key: {key}")
                return False
        
        return True
    except Exception as e:
        print(f"Report validation error: {e}")
        return False


def main():
    """
    Main function to handle command-line arguments
    """
    parser = argparse.ArgumentParser(description="Analyse IaC security findings")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--check-file", required=True, help="Path to Checkov checks JSON")
    parser.add_argument("--output", required=True, help="Output JSON file for security report")
    
    args = parser.parse_args()
    
    # Run analysis
    security_metrics = analyse_security(
        args.tool,
        args.check_file,
        args.output
    )
    
    # Validate the generated report
    if not validate_report(args.output):
        print("Security report validation failed")
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()