#!/usr/bin/env python3
"""
Simplified report generator for IaC tools evaluation
"""

import argparse
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json_file(file_path, default=None):
    """Load JSON file with error handling"""
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return default
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return default

def generate_report(complexity_dir, security_dir, deployment_dir, performance_dir, cost_dir, output_dir):
    """Generate a simplified report comparing IaC tools"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Define tools and categories
    tools = ["terraform", "cloudformation", "opentofu"]
    categories = ["complexity", "security", "deployment", "performance", "cost"]
    
    # Initialize report structure
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tools_compared": tools,
        "categories": categories,
        "results": {},
        "rankings": {},
        "overall_ranking": {}
    }
    
    # Load data for each tool
    for tool in tools:
        report["results"][tool] = {}
        
        # Load data from each category
        report["results"][tool]["complexity"] = load_json_file(
            os.path.join(complexity_dir, tool, f"{tool}_report.json"), {})
        
        report["results"][tool]["security"] = load_json_file(
            os.path.join(security_dir, tool, f"{tool}_security_report.json"), {})
        
        report["results"][tool]["deployment"] = load_json_file(
            os.path.join(deployment_dir, tool, "deployment_report.json"), {})
        
        report["results"][tool]["performance"] = load_json_file(
            os.path.join(performance_dir, tool, "performance_report.json"), {})
        
        report["results"][tool]["cost"] = load_json_file(
            os.path.join(cost_dir, tool, "cost_report.json"), {})
    
    # Calculate rankings
    score_keys = {
        "complexity": "complexity_score",
        "security": "overall.security_score",
        "deployment": "overall.efficiency_score",
        "performance": "summary.performance_score",
        "cost": "cost_efficiency_score"
    }
    
    # Generate rankings for each category
    for category in categories:
        report["rankings"][category] = {}
        scores = {}
        
        for tool in tools:
            if category in report["results"][tool]:
                # Extract score based on category
                score_key = score_keys.get(category)
                if score_key:
                    # Handle nested keys
                    if '.' in score_key:
                        parts = score_key.split('.')
                        value = report["results"][tool][category]
                        for part in parts:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                value = 0
                                break
                        scores[tool] = value if isinstance(value, (int, float)) else 0
                    else:
                        scores[tool] = report["results"][tool][category].get(score_key, 0)
        
        # Sort tools by score (higher is better)
        sorted_tools = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Assign ranks
        for i, (tool, score) in enumerate(sorted_tools):
            report["rankings"][category][tool] = {
                "rank": i + 1,
                "score": score
            }
    
    # Generate overall ranking
    weights = {
        "complexity": 0.15,
        "security": 0.25,
        "deployment": 0.25,
        "performance": 0.2,
        "cost": 0.15
    }
    
    # Calculate weighted scores for overall ranking
    overall_scores = {}
    for category, category_rankings in report["rankings"].items():
        weight = weights.get(category, 0.2)
        for tool, rank_data in category_rankings.items():
            if tool not in overall_scores:
                overall_scores[tool] = 0
            
            # Convert rank to points (1st = 100, 2nd = 90, 3rd = 80)
            rank_points = max(0, 110 - (rank_data["rank"] * 10))
            overall_scores[tool] += weight * rank_points
    
    # Sort tools by overall score
    sorted_tools = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Assign overall ranks
    for i, (tool, score) in enumerate(sorted_tools):
        report["overall_ranking"][tool] = {
            "rank": i + 1,
            "score": round(score, 2)
        }
    
    # Save the JSON report
    report_file = os.path.join(output_dir, "report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate charts
    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    # Generate charts
    generate_charts(report, charts_dir)
    
    logger.info("Report generation completed")
    logger.info(f"Report saved to: {report_file}")
    logger.info(f"Charts saved to: {charts_dir}")
    
    return report

def generate_charts(report, charts_dir):
    """Generate visualization charts for the report"""
    try:
        # 1. Overall ranking chart
        generate_overall_ranking_chart(report, charts_dir)
        
        # 2. Category scores chart
        generate_category_scores_chart(report, charts_dir)
        
        # 3. Performance comparison
        generate_performance_comparison(report, charts_dir)
        
        # 4. Cost comparison
        generate_cost_comparison(report, charts_dir)
    except Exception as e:
        logger.error(f"Error generating charts: {str(e)}")

def generate_overall_ranking_chart(report, charts_dir):
    """Generate chart showing overall ranking"""
    try:
        tools = []
        scores = []
        
        # Sort by rank
        for tool, data in sorted(report["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
            tools.append(tool.capitalize())
            scores.append(data["score"])
        
        plt.figure(figsize=(10, 6))
        bars = plt.barh(tools, scores, color=['#1f77b4', '#ff7f0e', '#2ca02c'][:len(tools)])
        
        # Add score labels
        for bar, score in zip(bars, scores):
            plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                    f'{score:.2f}', va='center')
        
        plt.title('Overall IaC Tool Ranking', fontsize=16)
        plt.xlabel('Score (higher is better)', fontsize=14)
        plt.ylabel('Tool', fontsize=14)
        plt.grid(axis='x', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, 'overall_ranking.png'))
        plt.close()
    except Exception as e:
        logger.error(f"Error generating overall ranking chart: {str(e)}")

def generate_category_scores_chart(report, charts_dir):
    """Generate chart comparing tool scores across categories"""
    try:
        categories = report["categories"]
        tools = report["tools_compared"]
        
        # Extract scores for each tool and category
        scores = {}
        for tool in tools:
            scores[tool] = []
            for category in categories:
                if category in report["rankings"] and tool in report["rankings"][category]:
                    scores[tool].append(report["rankings"][category][tool]["score"])
                else:
                    scores[tool].append(0)
        
        # Create DataFrame
        df = pd.DataFrame(scores, index=categories)
        
        plt.figure(figsize=(12, 8))
        ax = df.plot(kind='bar', figsize=(12, 8), width=0.7)
        
        plt.title('IaC Tools Comparison by Category', fontsize=16)
        plt.xlabel('Category', fontsize=14)
        plt.ylabel('Score (higher is better)', fontsize=14)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(title='Tool', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, 'category_scores.png'))
        plt.close()
    except Exception as e:
        logger.error(f"Error generating category scores chart: {str(e)}")

def generate_performance_comparison(report, charts_dir):
    """Generate chart comparing performance metrics"""
    try:
        tools = report["tools_compared"]
        
        # Extract performance metrics
        execution_times = []
        cpu_peaks = []
        memory_peaks = []
        
        for tool in tools:
            if "performance" in report["results"].get(tool, {}) and report["results"][tool]["performance"]:
                perf_data = report["results"][tool]["performance"]
                
                if "summary" in perf_data:
                    execution_times.append(perf_data["summary"].get("avg_duration", 0))
                    cpu_peaks.append(perf_data["summary"].get("avg_cpu_peak", 0))
                    memory_peaks.append(perf_data["summary"].get("avg_memory_peak", 0))
                else:
                    execution_times.append(0)
                    cpu_peaks.append(0)
                    memory_peaks.append(0)
            else:
                execution_times.append(0)
                cpu_peaks.append(0)
                memory_peaks.append(0)
        
        # Create bar charts
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
        
        # Format tool names
        tool_names = [t.capitalize() for t in tools]
        
        # Execution time chart
        ax1.bar(tool_names, execution_times, color='skyblue')
        ax1.set_title('Average Operation Execution Time')
        ax1.set_ylabel('Seconds')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # CPU peak chart
        ax2.bar(tool_names, cpu_peaks, color='lightcoral')
        ax2.set_title('Peak CPU Usage')
        ax2.set_ylabel('CPU %')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Memory peak chart
        ax3.bar(tool_names, memory_peaks, color='lightgreen')
        ax3.set_title('Peak Memory Usage')
        ax3.set_ylabel('Memory (MB)')
        ax3.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, 'performance_comparison.png'))
        plt.close()
    except Exception as e:
        logger.error(f"Error generating performance comparison chart: {str(e)}")

def generate_cost_comparison(report, charts_dir):
    """Generate a chart comparing cost metrics"""
    try:
        tools = report["tools_compared"]
        
        # Extract cost metrics
        monthly_costs = []
        opportunity_counts = []
        
        for tool in tools:
            if "cost" in report["results"].get(tool, {}) and report["results"][tool]["cost"]:
                cost_data = report["results"][tool]["cost"]
                monthly_costs.append(cost_data.get("monthly_cost", 0))
                opportunity_counts.append(len(cost_data.get("cost_optimization_opportunities", [])))
            else:
                monthly_costs.append(0)
                opportunity_counts.append(0)
        
        # Format tool names
        tool_names = [t.capitalize() for t in tools]
        
        # Create charts
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Monthly cost chart
        ax1.bar(tool_names, monthly_costs, color='skyblue')
        ax1.set_title('Estimated Monthly Cost')
        ax1.set_ylabel('USD ($)')
        ax1.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Cost optimization opportunities chart
        ax2.bar(tool_names, opportunity_counts, color='lightcoral')
        ax2.set_title('Cost Optimization Opportunities')
        ax2.set_ylabel('Count')
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, 'cost_comparison.png'))
        plt.close()
    except Exception as e:
        logger.error(f"Error generating cost comparison chart: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate IaC evaluation report")
    parser.add_argument("--complexity-dir", required=True, help="Directory containing complexity results")
    parser.add_argument("--security-dir", required=True, help="Directory containing security results")
    parser.add_argument("--deployment-dir", required=True, help="Directory containing deployment results")
    parser.add_argument("--performance-dir", required=True, help="Directory containing performance results")
    parser.add_argument("--cost-dir", required=True, help="Directory containing cost results")
    parser.add_argument("--output-dir", required=True, help="Directory to save the final report")
    
    args = parser.parse_args()
    
    generate_report(
        args.complexity_dir,
        args.security_dir,
        args.deployment_dir,
        args.performance_dir,
        args.cost_dir,
        args.output_dir
    )