#!/usr/bin/env python3
"""
Resource Monitor - Tracks CPU, memory, and disk usage during command execution
"""

import argparse
import json
import os
import psutil
import subprocess
import sys
import time
from datetime import datetime


def get_system_metrics():
    """Captures current system resource metrics"""
    return {
        "timestamp": time.time(),
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "memory_used_mb": psutil.virtual_memory().used / (1024 * 1024),
        "disk_percent": psutil.disk_usage('/').percent,
    }


def monitor_command(command, output_file, interval=1.0):
    """
    Executes a command and monitors system resources while it's running
    
    Args:
        command (str): The command to execute
        output_file (str): Path to save the metrics JSON
        interval (float): Sampling interval in seconds
    
    Returns:
        dict: Execution metrics including exit code and execution time
    """
    metrics = []
    
    print(f"Starting execution of: {command}")
    print(f"Recording metrics every {interval} seconds")
    
    # Record initial state
    metrics.append(get_system_metrics())
    
    # Start the process
    start_time = time.time()
    process = subprocess.Popen(command, shell=True)
    
    # Monitor while running
    try:
        while process.poll() is None:
            metrics.append(get_system_metrics())
            time.sleep(interval)
    except KeyboardInterrupt:
        process.kill()
        print("Monitoring interrupted by user")
    
    # Record final state
    metrics.append(get_system_metrics())
    end_time = time.time()
    
    # Calculate stats
    cpu_values = [m["cpu_percent"] for m in metrics]
    memory_values = [m["memory_used_mb"] for m in metrics]
    
    results = {
        "command": command,
        "start_time": start_time,
        "end_time": end_time,
        "execution_time_seconds": end_time - start_time,
        "exit_code": process.returncode,
        "metrics": metrics,
        "summary": {
            "cpu_percent": {
                "min": min(cpu_values),
                "max": max(cpu_values),
                "avg": sum(cpu_values) / len(cpu_values)
            },
            "memory_mb": {
                "min": min(memory_values),
                "max": max(memory_values),
                "avg": sum(memory_values) / len(memory_values),
                "peak": max(memory_values)
            }
        }
    }
    
    # Save the metrics
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Execution completed in {results['execution_time_seconds']:.2f} seconds")
    print(f"Peak CPU: {results['summary']['cpu_percent']['max']:.1f}%")
    print(f"Peak Memory: {results['summary']['memory_mb']['max']:.1f} MB")
    print(f"Metrics saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor system resources during command execution")
    parser.add_argument("--command", required=True, help="Command to execute and monitor")
    parser.add_argument("--output", required=True, help="Output JSON file for metrics")
    parser.add_argument("--interval", type=float, default=1.0, help="Sampling interval in seconds")
    
    args = parser.parse_args()
    
    monitor_command(args.command, args.output, args.interval)