#!/usr/bin/env python3
"""
Generate charts from resource usage data
"""

import argparse
import json
import os
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime


def load_resource_data(file_path):
    """Load resource monitoring data from a JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def create_time_series_chart(metrics, title, output_file):
    """Create a time series chart from metrics data"""
    # Extract time series data
    timestamps = [m['timestamp'] for m in metrics]
    
    # Convert timestamps to relative seconds
    start_time = timestamps[0]
    relative_times = [(t - start_time) for t in timestamps]
    
    cpu_values = [m['cpu_percent'] for m in metrics]
    memory_values = [m['memory_used_mb'] for m in metrics]
    
    # Create a pandas DataFrame for easier plotting
    df = pd.DataFrame({
        'time': relative_times,
        'cpu_percent': cpu_values,
        'memory_mb': memory_values
    })
    
    # Plot the data
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # CPU Plot
    ax1.plot(df['time'], df['cpu_percent'], 'b-', linewidth=2)
    ax1.set_ylabel('CPU Usage (%)')
    ax1.set_title(f'{title} - Resource Usage')
    ax1.grid(True)
    ax1.set_ylim(0, max(100, max(df['cpu_percent']) * 1.1))
    
    # Memory Plot
    ax2.plot(df['time'], df['memory_mb'], 'r-', linewidth=2)
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Memory (MB)')
    ax2.grid(True)
    ax2.set_ylim(0, max(df['memory_mb']) * 1.1)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def create_summary_chart(data_files, tool, output_dir):
    """Create a summary comparison chart of different operations"""
    operations = []
    cpu_peaks = []
    memory_peaks = []
    durations = []
    
    for file_path in data_files:
        # Parse operation name from filename
        operation = os.path.basename(file_path).replace('_performance.json', '').replace('_resources.json', '')
        
        # Load data
        data = load_resource_data(file_path)
        
        # Extract metrics
        operations.append(operation)
        cpu_peaks.append(data['summary']['cpu_percent']['max'])
        memory_peaks.append(data['summary']['memory_mb']['max'])
        durations.append(data['execution_time_seconds'])
    
    # Create DataFrame
    df = pd.DataFrame({
        'Operation': operations,
        'CPU Peak (%)': cpu_peaks,
        'Memory Peak (MB)': memory_peaks,
        'Duration (s)': durations
    })
    
    # Create bar charts
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    
    # CPU Chart
    ax1.bar(df['Operation'], df['CPU Peak (%)'], color='skyblue')
    ax1.set_ylabel('CPU Peak (%)')
    ax1.set_title(f'{tool.capitalize()} - Peak Resource Usage by Operation')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Memory Chart
    ax2.bar(df['Operation'], df['Memory Peak (MB)'], color='lightcoral')
    ax2.set_ylabel('Memory Peak (MB)')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Duration Chart
    ax3.bar(df['Operation'], df['Duration (s)'], color='lightgreen')
    ax3.set_ylabel('Duration (s)')
    ax3.set_xlabel('Operation')
    ax3.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'{tool}_operation_comparison.png'))
    plt.close()
    
    # Also save the data as CSV for further analysis
    df.to_csv(os.path.join(output_dir, f'{tool}_operation_metrics.csv'), index=False)
    return df


def main():
    parser = argparse.ArgumentParser(description="Generate resource usage charts")
    parser.add_argument("--data-dir", required=True, help="Directory containing resource monitoring JSON files")
    parser.add_argument("--output-dir", required=True, help="Directory to save charts")
    parser.add_argument("--tool", required=True, help="IaC tool name (terraform, cloudformation, opentofu)")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find all resource data files
    data_files = []
    for filename in os.listdir(args.data_dir):
        if filename.endswith('_resources.json') or filename.endswith('_performance.json'):
            data_files.append(os.path.join(args.data_dir, filename))
    
    print(f"Found {len(data_files)} resource data files")
    
    # Generate individual charts for each file
    for file_path in data_files:
        try:
            data = load_resource_data(file_path)
            base_name = os.path.basename(file_path).replace('.json', '')
            title = f"{args.tool.capitalize()} - {base_name.replace('_', ' ').title()}"
            output_file = os.path.join(args.output_dir, f"{base_name}_chart.png")
            
            create_time_series_chart(data['metrics'], title, output_file)
            print(f"Generated chart: {output_file}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Generate summary comparison chart
    if data_files:
        try:
            summary_df = create_summary_chart(data_files, args.tool, args.output_dir)
            print(f"Generated summary comparison chart and CSV")
            print(summary_df)
        except Exception as e:
            print(f"Error generating summary chart: {e}")


if __name__ == "__main__":
    main()