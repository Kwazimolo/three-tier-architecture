#!/usr/bin/env python3
"""
Simple script to generate deployment metrics summary without performance monitoring
"""

import argparse
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_tool_deployment(data_dir, output_dir, tool):
    """Process deployment data for a specific tool"""
    logger.info(f"Processing deployment data for {tool}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if deployment data exists
    deployment_file = os.path.join(data_dir, "deployment_report.json")
    
    if not os.path.exists(deployment_file):
        logger.warning(f"No deployment report found for {tool}")
        # Create an empty report to avoid errors
        deployment_report = {
            "tool": tool,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall": {
                "total_time_seconds": 0,
                "efficiency_score": 0,
                "success": False
            }
        }
    else:
        # Load existing report
        try:
            with open(deployment_file, 'r') as f:
                deployment_report = json.load(f)
            logger.info(f"Loaded deployment report for {tool}")
        except Exception as e:
            logger.error(f"Error reading deployment report for {tool}: {e}")
            deployment_report = {
                "tool": tool,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "overall": {
                    "total_time_seconds": 0,
                    "efficiency_score": 0,
                    "success": False
                }
            }
    
    # Save the report
    report_path = os.path.join(output_dir, "deployment_report.json")
    with open(report_path, 'w') as f:
        json.dump(deployment_report, f, indent=2)
    
    logger.info(f"Saved deployment report for {tool} at {report_path}")
    
    return deployment_report

def main():
    parser = argparse.ArgumentParser(description="Process deployment metrics")
    parser.add_argument("--data-dir", required=True, help="Base directory containing deployment data")
    parser.add_argument("--output-dir", required=True, help="Directory to save reports")
    
    args = parser.parse_args()
    
    # Define tools to process
    tools = ["terraform", "cloudformation", "opentofu"]
    
    # Process each tool
    for tool in tools:
        tool_data_dir = os.path.join(args.data_dir, tool)
        tool_output_dir = os.path.join(args.output_dir, tool)
        
        process_tool_deployment(tool_data_dir, tool_output_dir, tool)

if __name__ == "__main__":
    main()