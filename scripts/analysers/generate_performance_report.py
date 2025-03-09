#!/usr/bin/env python3
"""
Generates a comprehensive performance report for an IaC tool
"""

import argparse
import json
import os
import glob


def generate_performance_report(tool, data_dir, output_file):
    """
    Generates a comprehensive performance report from individual test results
    
    Args:
        tool (str): The IaC tool (terraform, cloudformation, opentofu)
        data_dir (str): Directory containing performance test results
        output_file (str): Where to save the performance report
    """
    # Find all performance test result files
    performance_files = glob.glob(os.path.join(data_dir, "*_performance.json"))
    
    # Load performance data
    performance_data = {}
    for file_path in performance_files:
        operation_name = os.path.basename(file_path).replace('_performance.json', '')
        with open(file_path, 'r') as f:
            performance_data[operation_name] = json.load(f)
    
    # Generate summary report
    performance_report = {
        "tool": tool,
        "operations": {},
        "summary": {
            "total_operations": len(performance_data),
            "fastest_operation": None,
            "slowest_operation": None,
            "highest_cpu_operation": None,
            "highest_memory_operation": None
        }
    }
    
    # Process each operation
    fastest_time = float('inf')
    slowest_time = 0
    highest_cpu = 0
    highest_memory = 0
    
    for operation, data in performance_data.items():
        # Extract key metrics
        execution_time = data.get('execution_time_seconds', 0)
        cpu_peak = data.get('summary', {}).get('cpu_percent', {}).get('max', 0)
        memory_peak = data.get('summary', {}).get('memory_mb', {}).get('max', 0)
        
        # Store operation metrics
        performance_report["operations"][operation] = {
            "execution_time": execution_time,
            "cpu_peak": cpu_peak,
            "memory_peak": memory_peak
        }
        
        # Update summary metrics
        if execution_time < fastest_time:
            fastest_time = execution_time
            performance_report["summary"]["fastest_operation"] = operation
            
        if execution_time > slowest_time:
            slowest_time = execution_time
            performance_report["summary"]["slowest_operation"] = operation
            
        if cpu_peak > highest_cpu:
            highest_cpu = cpu_peak
            performance_report["summary"]["highest_cpu_operation"] = operation
            
        if memory_peak > highest_memory:
            highest_memory = memory_peak
            performance_report["summary"]["highest_memory_operation"] = operation
    
    # Calculate overall performance score
    performance_report["summary"]["performance_score"] = calculate_performance_score(performance_report)
    
    # Save the report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(performance_report, f, indent=2)
    
    print(f"Performance report generated for {tool}")
    print(f"Total operations analysed: {performance_report['summary']['total_operations']}")
    print(f"Performance score: {performance_report['summary']['performance_score']}")
    
    return performance_report


def calculate_performance_score(report):
    """
    Calculate a performance score based on execution time and resource usage
    
    Returns a score from 0-100, where 100 is best performance
    """
    # If no operations, return 0
    if not report["operations"]:
        return 0
    
    # Calculate average metrics
    total_time = 0
    total_cpu = 0
    total_memory = 0
    
    for operation_data in report["operations"].values():
        total_time += operation_data["execution_time"]
        total_cpu += operation_data["cpu_peak"]
        total_memory += operation_data["memory_peak"]
    
    num_operations = len(report["operations"])
    avg_time = total_time / num_operations
    avg_cpu = total_cpu / num_operations
    avg_memory = total_memory / num_operations
    
    # Calculate score components (lower values are better)
    # Normalize to 0-100 scale
    time_score = 100 * min(1.0, 10 / max(1, avg_time))        # 10s or less is ideal
    cpu_score = 100 * min(1.0, 30 / max(1, avg_cpu))          # 30% CPU or less is ideal
    memory_score = 100 * min(1.0, 500 / max(1, avg_memory))   # 500MB or less is ideal
    
    # Weight the components (time is most important for performance)
    performance_score = (
        0.5 * time_score +
        0.25 * cpu_score +
        0.25 * memory_score
    )
    
    return round(performance_score, 2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate IaC performance report")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--data-dir", required=True, help="Directory containing performance test results")
    parser.add_argument("--output", required=True, help="Output JSON file for performance report")
    
    args = parser.parse_args()
    
    generate_performance_report(args.tool, args.data_dir, args.output)