#!/usr/bin/env python3
"""
analyses deployment metrics for IaC tools
"""

import argparse
import json
import os
import time


def analyse_deployment(tool, stack_name, resource_usage, init_resource_usage, cloudtrail_events, start_time, end_time, output_file):
    """
    analyses deployment metrics including time, resources, and API calls
    
    Args:
        tool (str): The IaC tool (terraform, cloudformation, opentofu)
        stack_name (str): Stack/deployment name
        resource_usage (str): Path to resource usage JSON for main deployment
        init_resource_usage (str): Path to resource usage JSON for init (if applicable)
        cloudtrail_events (str): Path to CloudTrail events JSON
        start_time (int): Deployment start time (epoch)
        end_time (int): Deployment end time (epoch)
        output_file (str): Where to save the deployment report
    """
    # Load resource usage data
    with open(resource_usage, 'r') as f:
        deployment_resources = json.load(f)
    
    # Load init resources if available
    init_resources = None
    if init_resource_usage and os.path.exists(init_resource_usage):
        with open(init_resource_usage, 'r') as f:
            init_resources = json.load(f)
    
    # Load CloudTrail events
    with open(cloudtrail_events, 'r') as f:
        cloudtrail_data = json.load(f)
    
    # Extract deployment metrics
    deployment_metrics = {
        "tool": tool,
        "stack_name": stack_name,
        "deployment_time": {
            "start": int(start_time),
            "end": int(end_time),
            "total_seconds": int(end_time) - int(start_time)
        },
        "resource_usage": {
            "deployment": {
                "execution_time": deployment_resources["execution_time_seconds"],
                "cpu": deployment_resources["summary"]["cpu_percent"],
                "memory": deployment_resources["summary"]["memory_mb"]
            }
        },
        "api_calls": analyse_api_calls(cloudtrail_data),
    }
    
    # Add init metrics if available
    if init_resources:
        deployment_metrics["resource_usage"]["init"] = {
            "execution_time": init_resources["execution_time_seconds"],
            "cpu": init_resources["summary"]["cpu_percent"],
            "memory": init_resources["summary"]["memory_mb"]
        }
    
    # Calculate overall metrics
    deployment_metrics["overall"] = calculate_overall_metrics(deployment_metrics)
    
    # Save the report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(deployment_metrics, f, indent=2)
    
    print(f"Deployment analysis completed for {tool}")
    print(f"Total deployment time: {deployment_metrics['deployment_time']['total_seconds']} seconds")
    print(f"Total API calls: {deployment_metrics['api_calls']['total_count']}")
    if 'init' in deployment_metrics['resource_usage']:
        print(f"Init time: {deployment_metrics['resource_usage']['init']['execution_time']} seconds")
    print(f"Deployment execution time: {deployment_metrics['resource_usage']['deployment']['execution_time']} seconds")
    
    return deployment_metrics


def analyse_api_calls(cloudtrail_data):
    """analyse API calls from CloudTrail events"""
    # Count API calls by service
    service_counts = {}
    
    for event in cloudtrail_data.get('Events', []):
        if isinstance(event, dict) and 'CloudTrailEvent' in event:
            try:
                cloud_trail_event = json.loads(event['CloudTrailEvent'])
                event_source = cloud_trail_event.get('eventSource', '')
                
                # Extract the service name from the event source
                if event_source:
                    service = event_source.split('.')[0]
                    service_counts[service] = service_counts.get(service, 0) + 1
            except (json.JSONDecodeError, KeyError):
                pass
    
    # Generate API call summary
    api_summary = {
        "service_breakdown": service_counts,
        "total_count": sum(service_counts.values())
    }
    
    return api_summary


def calculate_overall_metrics(metrics):
    """Calculate overall deployment metrics and score"""
    # Extract key performance indicators
    deployment_time = metrics['deployment_time']['total_seconds']
    cpu_peak = metrics['resource_usage']['deployment']['cpu']['max']
    memory_peak = metrics['resource_usage']['deployment']['memory']['max']
    api_calls = metrics['api_calls']['total_count']
    
    # Consider init time if available
    init_time = 0
    if 'init' in metrics['resource_usage']:
        init_time = metrics['resource_usage']['init']['execution_time']
    
    # Calculate efficiency score (lower is better)
    # Normalize each metric to a 0-100 scale where 100 is most efficient
    time_score = 100 * min(1.0, 300 / max(1, deployment_time))  # 300s (5min) or less is ideal
    cpu_score = 100 * min(1.0, 50 / max(1, cpu_peak))           # 50% CPU or less is ideal
    memory_score = 100 * min(1.0, 1000 / max(1, memory_peak))   # 1GB or less is ideal
    api_score = 100 * min(1.0, 100 / max(1, api_calls))         # 100 calls or less is ideal
    
    # Weight the scores (time and API calls are more important)
    efficiency_score = (
        0.4 * time_score +
        0.2 * cpu_score +
        0.2 * memory_score +
        0.2 * api_score
    )
    
    return {
        "total_time_seconds": deployment_time + init_time,
        "deployment_time_seconds": deployment_time,
        "init_time_seconds": init_time,
        "peak_cpu_percent": cpu_peak,
        "peak_memory_mb": memory_peak,
        "api_call_count": api_calls,
        "efficiency_score": round(efficiency_score, 2)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="analyse IaC deployment metrics")
    parser.add_argument("--tool", required=True, help="IaC tool (terraform, cloudformation, opentofu)")
    parser.add_argument("--stack-name", required=True, help="Stack/deployment name")
    parser.add_argument("--resource-usage", required=True, help="Path to resource usage JSON")
    parser.add_argument("--init-resource-usage", help="Path to init resource usage JSON (if applicable)")
    parser.add_argument("--cloudtrail-events", required=True, help="Path to CloudTrail events JSON")
    parser.add_argument("--start-time", required=True, help="Deployment start time (epoch)")
    parser.add_argument("--end-time", required=True, help="Deployment end time (epoch)")
    parser.add_argument("--output", required=True, help="Output JSON file for deployment report")
    
    args = parser.parse_args()
    
    analyse_deployment(
        args.tool,
        args.stack_name,
        args.resource_usage,
        args.init_resource_usage,
        args.cloudtrail_events,
        args.start_time,
        args.end_time,
        args.output
    )