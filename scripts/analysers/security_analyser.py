#!/usr/bin/env python3
"""
analyses security findings from Checkov for IaC code
"""

import argparse
import json
import os


def analyse_security(tool, aws_checks, iam_checks, network_checks, encryption_checks, output_file):
    """
    analyses security findings from Checkov
    
    Args:
        tool (str): The IaC tool (terraform, cloudformation, opentofu)
        aws_checks (str): Path to AWS best practices check results
        iam_checks (str): Path to IAM security check results
        network_checks (str): Path to network security check results
        encryption_checks (str): Path to encryption check results
        output_file (str): Where to save the security report
    """
    # Load check results
    with open(aws_checks, 'r') as f:
        aws_data = json.load(f)
    
    with open(iam_checks, 'r') as f:
        iam_data = json.load(f)
    
    with open(network_checks, 'r') as f:
        network_data = json.load(f)
    
    with open(encryption_checks, 'r') as f:
        encryption_data = json.load(f)
    
    # Process results
    security_metrics = {
        "tool": tool,
        "aws_best_practices": {
            "passed": len(aws_data['results'].get('passed_checks', [])),
            "failed": len(aws_data['results'].get('failed_checks', [])),
            "pass_percentage": calculate_pass_percentage(aws_data)
        },
        "iam_security": {
            "passed": len(iam_data['results'].get('passed_checks', [])),
            "failed": len(iam_data['results'].get('failed_checks', [])),
            "pass_percentage": calculate_pass_percentage(iam_data)
        },
        "network_security": {
            "passed": len(network_data['results'].get('passed_checks', [])),
            "failed": len(network_data['results'].get('failed_checks', [])),
            "pass_percentage": calculate_pass_percentage(network_data)
        },
        "encryption_security": {
            "passed": len(encryption_data['results'].get('passed_checks', [])),
            "failed": len(encryption_data['results'].get('failed_checks', [])),
            "pass_percentage": calculate_pass_percentage(encryption_data)
        }
    }
    
    # Calculate overall scores
    total_passed = (security_metrics["aws_best_practices"]["passed"] +
                   security_metrics["iam_security"]["passed"] +
                   security_metrics["network_security"]["passed"] +
                   security_metrics["encryption_security"]["passed"])
    
    total_failed = (security_metrics["aws_best_practices"]["failed"] +
                    security_metrics["iam_security"]["failed"] +
                    security_metrics["network_security"]["failed"] +
                    security_metrics["encryption_security"]["failed"])
    
    total_checks = total_passed + total_failed
    
    security_metrics["overall"] = {
        "total_checks": total_checks,
        "passed": total_passed,
        "failed": total_failed,
        "pass_percentage": 100 * total_passed / total_checks if total_checks > 0 else 0,
        "security_score": calculate_security_score(security_metrics)
    }
    
    # Extract common failure patterns
    security_metrics["common_failures"] = extract_common_failures(aws_data, iam_data, network_data, encryption_data)
    
    # Save the report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(security_metrics, f, indent=2)
    
    print(f"Security analysis completed for {tool}")
    print(f"Overall pass percentage: {security_metrics['overall']['pass_percentage']:.2f}%")
    print(f"Security score: {security_metrics['overall']['security_score']}")
    
    return security_metrics


def calculate_pass_percentage(checkov_data):
    """Calculate the percentage of passed checks"""
    passed = len(checkov_data['results'].get('passed_checks', []))
    failed = len(checkov_data['results'].get('failed_checks', []))
    total = passed + failed
    
    return 100 * passed / total if total > 0 else 0


def calculate_security_score(metrics):
    """
    Calculate a security score based on the weighted importance of different security aspects
    
    Returns a score from 0-100, where 100 is most secure
    """
    # Weights for different security aspects (totaling 100%)
    weights = {
        "aws_best_practices": 0.2,
        "iam_security": 0.3,        # IAM is most critical
        "network_security": 0.3,    # Network security equally important
        "encryption_security": 0.2
    }
    
    # Calculate weighted score
    score = (
        weights["aws_best_practices"] * metrics["aws_best_practices"]["pass_percentage"] +
        weights["iam_security"] * metrics["iam_security"]["pass_percentage"] +
        weights["network_security"] * metrics["network_security"]["pass_percentage"] +
        weights["encryption_security"] * metrics["encryption_security"]["pass_percentage"]
    )
    
    return round(score, 2)


def extract_common_failures(aws_data, iam_data, network_data, encryption_data):
    """Extract and categorize common security failures"""
    all_failures = []
    
    # Process each set of check results
    for data, category in [
        (aws_data, "AWS Best Practices"),
        (iam_data, "IAM Security"),
        (network_data, "Network Security"),
        (encryption_data, "Encryption")
    ]:
        for check in data['results'].get('failed_checks', []):
            all_failures.append({
                "category": category,
                "check_id": check.get('check_id', ''),
                "check_name": check.get('check_name', ''),
                "resource": check.get('resource', ''),
                "guideline": check.get('guideline', '')
            })
    
    # Group failures by check_id to find common patterns
    failure_counts = {}
    for failure in all_failures:
        check_id = failure['check_id']
        if check_id not in failure_counts:
            failure_counts[check_id] = {
                "count": 0,
                "check_name": failure['check_name'],
                "category": failure['category'],
                "guideline": failure['guideline']
            }
        failure_counts[check_id]["count"] += 1
    
    # Sort by frequency
    sorted_failures = sorted(
        [{"check_id": k, **v} for k, v in failure_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    
    return sorted_failures[:10]  # Return top 10 failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="analyse IaC security findings")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--aws-checks", required=True, help="Path to AWS checks JSON")
    parser.add_argument("--iam-checks", required=True, help="Path to IAM checks JSON")
    parser.add_argument("--network-checks", required=True, help="Path to network checks JSON")
    parser.add_argument("--encryption-checks", required=True, help="Path to encryption checks JSON")
    parser.add_argument("--output", required=True, help="Output JSON file for security report")
    
    args = parser.parse_args()
    
    analyse_security(
        args.tool,
        args.aws_checks,
        args.iam_checks,
        args.network_checks,
        args.encryption_checks,
        args.output
    )