#!/usr/bin/env python3
"""
Generate charts from resource usage data for IaC tools comparison
"""

import argparse
import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_resource_data(file_path):
    """Load resource monitoring data from a JSON file with error handling"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None

def create_time_series_chart(metrics, title, output_file):
    """Create a time series chart from metrics data"""
    if not metrics:
        logger.warning(f"No metrics data for {title}, skipping chart generation")
        return
    
    try:
        # Extract time series data
        timestamps = [m.get('timestamp', 0) for m in metrics]
        
        # Convert timestamps to relative seconds
        if timestamps and timestamps[0]:
            start_time = timestamps[0]
            relative_times = [(t - start_time) for t in timestamps]
        else:
            relative_times = list(range(len(metrics)))
        
        cpu_values = [m.get('cpu_percent', 0) for m in metrics]
        memory_values = [m.get('memory_used_mb', 0) for m in metrics]
        
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
        ax1.set_ylim(0, max(100, max(df['cpu_percent']) * 1.1) if df['cpu_percent'].any() else 100)
        
        # Memory Plot
        ax2.plot(df['time'], df['memory_mb'], 'r-', linewidth=2)
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Memory (MB)')
        ax2.grid(True)
        ax2.set_ylim(0, max(df['memory_mb']) * 1.1 if df['memory_mb'].any() else 100)
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        logger.info(f"Created time series chart: {output_file}")
        
    except Exception as e:
        logger.error(f"Error creating time series chart for {title}: {str(e)}")

def create_summary_chart(data_files, tool, output_dir):
    """Create a summary comparison chart of different operations"""
    if not data_files:
        logger.warning(f"No data files for {tool}, skipping summary chart generation")
        return None
    
    try:
        operations = []
        cpu_peaks = []
        memory_peaks = []
        durations = []
        
        for file_path in data_files:
            # Parse operation name from filename
            operation = os.path.basename(file_path).replace('_performance.json', '').replace('_resources.json', '')
            
            # Load data
            data = load_resource_data(file_path)
            if not data:
                continue
                
            # Extract metrics
            operations.append(operation)
            cpu_peaks.append(data.get('summary', {}).get('cpu_percent', {}).get('max', 0))
            memory_peaks.append(data.get('summary', {}).get('memory_mb', {}).get('max', 0))
            durations.append(data.get('execution_time_seconds', 0))
        
        if not operations:
            logger.warning(f"No valid operation data for {tool}")
            return None
            
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
        ax1.tick_params(axis='x', rotation=45)
        
        # Memory Chart
        ax2.bar(df['Operation'], df['Memory Peak (MB)'], color='lightcoral')
        ax2.set_ylabel('Memory Peak (MB)')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        ax2.tick_params(axis='x', rotation=45)
        
        # Duration Chart
        ax3.bar(df['Operation'], df['Duration (s)'], color='lightgreen')
        ax3.set_ylabel('Duration (s)')
        ax3.set_xlabel('Operation')
        ax3.grid(axis='y', linestyle='--', alpha=0.7)
        ax3.tick_params(axis='x', rotation=45)
        
        # Adjust layout and save
        plt.tight_layout()
        chart_path = os.path.join(output_dir, f'{tool}_operation_comparison.png')
        plt.savefig(chart_path)
        plt.close()
        
        # Also save the data as CSV for further analysis
        csv_path = os.path.join(output_dir, f'{tool}_operation_metrics.csv')
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Created summary chart for {tool} at {chart_path}")
        logger.info(f"Saved metrics CSV at {csv_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error creating summary chart for {tool}: {str(e)}")
        return None

def process_tool_performance(data_dir, output_dir, tool):
    """Process performance data for a specific tool"""
    logger.info(f"Processing performance data for {tool}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all resource data files
    data_files = []
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith('_resources.json') or filename.endswith('_performance.json'):
                data_files.append(os.path.join(data_dir, filename))
    
    logger.info(f"Found {len(data_files)} resource data files for {tool}")
    
    # Generate individual charts for each file
    for file_path in data_files:
        try:
            data = load_resource_data(file_path)
            if not data or 'metrics' not in data:
                logger.warning(f"Missing or invalid data in {file_path}")
                continue
                
            base_name = os.path.basename(file_path).replace('.json', '')
            title = f"{tool.capitalize()} - {base_name.replace('_', ' ').title()}"
            output_file = os.path.join(output_dir, f"{base_name}_chart.png")
            
            create_time_series_chart(data['metrics'], title, output_file)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Generate summary comparison chart
    if data_files:
        try:
            summary_df = create_summary_chart(data_files, tool, output_dir)
            if summary_df is not None:
                # Create a performance summary report
                summary_report = {
                    "tool": tool,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "summary": {
                        "total_operations": len(summary_df),
                        "avg_duration": summary_df['Duration (s)'].mean(),
                        "max_duration": summary_df['Duration (s)'].max(),
                        "avg_cpu_peak": summary_df['CPU Peak (%)'].mean(),
                        "avg_memory_peak": summary_df['Memory Peak (MB)'].mean(),
                        "performance_score": calculate_performance_score(summary_df),
                        "fastest_operation": summary_df.loc[summary_df['Duration (s)'].idxmin(), 'Operation'] if not summary_df.empty else "N/A",
                        "slowest_operation": summary_df.loc[summary_df['Duration (s)'].idxmax(), 'Operation'] if not summary_df.empty else "N/A"
                    },
                    "operations": {}
                }
                
                # Add individual operation details
                for _, row in summary_df.iterrows():
                    op_name = row['Operation']
                    summary_report["operations"][op_name] = {
                        "execution_time": row['Duration (s)'],
                        "cpu_peak": row['CPU Peak (%)'],
                        "memory_peak": row['Memory Peak (MB)']
                    }
                
                # Save performance report
                report_path = os.path.join(output_dir, "performance_report.json")
                with open(report_path, 'w') as f:
                    json.dump(summary_report, f, indent=2)
                
                logger.info(f"Generated performance report: {report_path}")
                logger.info(f"Performance summary for {tool}:\n{summary_df}")
                
        except Exception as e:
            logger.error(f"Error generating summary for {tool}: {e}")

def calculate_performance_score(df):
    """Calculate a performance score based on the metrics"""
    if df.empty:
        return 0
        
    try:
        # Normalize metrics (lower is better for all metrics)
        max_duration = df['Duration (s)'].max()
        max_cpu = df['CPU Peak (%)'].max()
        max_memory = df['Memory Peak (MB)'].max()
        
        if max_duration == 0 or max_cpu == 0 or max_memory == 0:
            return 0
            
        avg_normalized_duration = 1 - (df['Duration (s)'].mean() / max_duration) * 0.5  # 50% weight
        avg_normalized_cpu = 1 - (df['CPU Peak (%)'].mean() / max_cpu) * 0.3  # 30% weight
        avg_normalized_memory = 1 - (df['Memory Peak (MB)'].mean() / max_memory) * 0.2  # 20% weight
        
        # Final score (0-100, higher is better)
        score = (avg_normalized_duration + avg_normalized_cpu + avg_normalized_memory) * 100
        return max(0, min(100, score))  # Clamp to 0-100 range
        
    except Exception as e:
        logger.error(f"Error calculating performance score: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description="Generate resource usage charts")
    parser.add_argument("--data-dir", required=True, help="Base directory containing resource data")
    parser.add_argument("--output-dir", required=True, help="Directory to save charts and reports")
    
    args = parser.parse_args()
    
    # Define tools to process
    tools = ["terraform", "cloudformation", "opentofu"]
    
    # Process each tool
    for tool in tools:
        tool_data_dir = os.path.join(args.data_dir, tool)
        tool_output_dir = os.path.join(args.output_dir, tool)
        
        process_tool_performance(tool_data_dir, tool_output_dir, tool)

if __name__ == "__main__":
    main()