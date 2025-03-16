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
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading {file_path}: {e}")
        return {}


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
    
    # Ensure we have data in the expected format
    results = checkov_data.get('results', checkov_data)
    
    # Categorise checks
    security_categories = {
        "aws_best_practices": [],
        "iam_security": [],
        "network_security": [],
        "encryption_security": []
    }
    
    # Process each check
    passed_checks = results.get('passed_checks', [])
    failed_checks = results.get('failed_checks', [])
    
    for check in passed_checks + failed_checks:
        check_name = check.get('check_name', '').lower()
        category = "aws_best_practices"
        
        if "iam" in check_name:
            category = "iam_security"
        elif "network" in check_name or "vpc" in check_name:
            category = "network_security"
        elif "encrypt" in check_name or "encryption" in check_name:
            category = "encryption_security"
        
        # Store the check
        security_categories[category].append(check)
    
    # Calculate security metrics
    security_metrics = {
        "tool": tool,
        "aws_best_practices": categorise_checks(security_categories["aws_best_practices"]),
        "iam_security": categorise_checks(security_categories["iam_security"]),
        "network_security": categorise_checks(security_categories["network_security"]),
        "encryption_security": categorise_checks(security_categories["encryption_security"])
    }
    
    # Calculate overall scores
    security_metrics["overall"] = calculate_overall_security(security_metrics)
    
    # Extract common failures
    security_metrics["common_failures"] = extract_common_failures(results.get('failed_checks', []))
    
    # Save the report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(security_metrics, f, indent=2)
    
    print(f"Security analysis completed for {tool}")
    print(f"Overall pass percentage: {security_metrics['overall']['pass_percentage']:.2f}%")
    print(f"Security score: {security_metrics['overall']['security_score']}")
    
    return security_metrics


def categorise_checks(checks):
    """
    Categorise and count security checks
    
    Args:
        checks (list): List of security checks
    
    Returns:
        dict: Categorised check metrics
    """
    passed = [c for c in checks if c.get('check_result', {}).get('result') == 'PASSED']
    failed = [c for c in checks if c.get('check_result', {}).get('result') == 'FAILED']
    
    total = len(passed) + len(failed)
    pass_percentage = 100 * len(passed) / total if total > 0 else 0
    
    return {
        "passed": len(passed),
        "failed": len(failed),
        "pass_percentage": round(pass_percentage, 2)
    }


def calculate_overall_security(metrics):
    """
    Calculate overall security score
    
    Args:
        metrics (dict): Security metrics for different categories
    
    Returns:
        dict: Overall security metrics
    """
    # Weights for different security aspects (totaling 100%)
    weights = {
        "aws_best_practices": 0.2,
        "iam_security": 0.3,
        "network_security": 0.3,
        "encryption_security": 0.2
    }
    
    # Calculate weighted score
    score = sum(
        weights[category] * data['pass_percentage']
        for category, data in metrics.items()
        if category != 'overall'
    )
    
    total_passed = sum(
        data['passed'] for category, data in metrics.items()
        if category != 'overall'
    )
    total_failed = sum(
        data['failed'] for category, data in metrics.items()
        if category != 'overall'
    )
    total_checks = total_passed + total_failed
    
    return {
        "total_checks": total_checks,
        "passed": total_passed,
        "failed": total_failed,
        "pass_percentage": round(100 * total_passed / total_checks, 2) if total_checks > 0 else 0,
        "security_score": round(score, 2)
    }


def extract_common_failures(failed_checks):
    """
    Extract and categorize common security failures
    
    Args:
        failed_checks (list): List of failed security checks
    
    Returns:
        list: Sorted list of common failures
    """
    failure_counts = {}
    
    for check in failed_checks:
        check_id = check.get('check_id', '')
        if not check_id:
            continue
        
        if check_id not in failure_counts:
            failure_counts[check_id] = {
                "count": 0,
                "check_name": check.get('check_name', ''),
                "resource_types": set(),
                "guideline": check.get('guideline', '')
            }
        
        failure_counts[check_id]["count"] += 1
        failure_counts[check_id]["resource_types"].add(check.get('resource_type', ''))
    
    # Convert resource_types to list and sort failures
    for failure in failure_counts.values():
        failure["resource_types"] = list(failure["resource_types"])
    
    # Sort by frequency and convert to list
    sorted_failures = sorted(
        [{"check_id": k, **v} for k, v in failure_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    
    return sorted_failures[:10]  # Return top 10 failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse IaC security findings")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--check-file", required=True, help="Path to Checkov checks JSON")
    parser.add_argument("--output", required=True, help="Output JSON file for security report")
    
    args = parser.parse_args()
    
    analyse_security(
        args.tool,
        args.check_file,
        args.output
    )