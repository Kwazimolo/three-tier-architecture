#!/usr/bin/env python3
"""
Generates the final comprehensive report comparing all IaC tools
"""

import argparse
import json
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime


def generate_report(complexity_dir, security_dir, deployment_dir, performance_dir, cost_dir, output_dir):
    """
    Generates a comprehensive report comparing IaC tools
    
    Args:
        complexity_dir (str): Directory containing complexity results
        security_dir (str): Directory containing security results
        deployment_dir (str): Directory containing deployment results
        performance_dir (str): Directory containing performance results
        cost_dir (str): Directory containing cost results
        output_dir (str): Where to save the final report
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize report structure
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tools_compared": ["terraform", "cloudformation", "opentofu"],
        "categories": ["complexity", "security", "deployment", "performance", "cost"],
        "results": {},
        "rankings": {},
        "overall_ranking": {}
    }
    
    # Process results for each tool
    for tool in report["tools_compared"]:
        report["results"][tool] = {}
        
        # Load complexity results
        complexity_file = os.path.join(complexity_dir, tool, f"{tool}_report.json")
        if os.path.exists(complexity_file):
            with open(complexity_file, 'r') as f:
                report["results"][tool]["complexity"] = json.load(f)
        
        # Load security results
        security_file = os.path.join(security_dir, tool, f"{tool}_security_report.json")
        if os.path.exists(security_file):
            with open(security_file, 'r') as f:
                report["results"][tool]["security"] = json.load(f)
        
        # Load deployment results
        deployment_file = os.path.join(deployment_dir, tool, "deployment_report.json")
        if os.path.exists(deployment_file):
            with open(deployment_file, 'r') as f:
                report["results"][tool]["deployment"] = json.load(f)
        
        # Load performance results
        performance_file = os.path.join(performance_dir, tool, "performance_report.json")
        if os.path.exists(performance_file):
            with open(performance_file, 'r') as f:
                report["results"][tool]["performance"] = json.load(f)
        
        # Load cost results
        cost_file = os.path.join(cost_dir, tool, "cost_report.json")
        if os.path.exists(cost_file):
            with open(cost_file, 'r') as f:
                report["results"][tool]["cost"] = json.load(f)
    
    # Generate rankings for each category
    for category in report["categories"]:
        rankings = generate_category_rankings(report["results"], category)
        report["rankings"][category] = rankings
    
    # Generate overall ranking
    report["overall_ranking"] = generate_overall_ranking(report["rankings"])
    
    # Generate visualizations
    generate_visualizations(report, output_dir)
    
    # Save the report
    report_file = os.path.join(output_dir, "report.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Generate HTML report
    generate_html_report(report, output_dir)
    
    print("Final report generation completed")
    print(f"Report saved to: {report_file}")
    
    return report


def generate_category_rankings(results, category):
    """Generate rankings for a specific category"""
    rankings = {}
    
    # Different scoring keys for different categories
    score_keys = {
        "complexity": "complexity_score",
        "security": "overall.security_score",
        "deployment": "overall.efficiency_score",
        "performance": "summary.performance_score",
        "cost": "cost_efficiency_score"
    }
    
    # Get scores for each tool
    scores = {}
    for tool, tool_results in results.items():
        if category in tool_results:
            # Extract score based on category
            score_key = score_keys.get(category)
            if score_key:
                # Handle nested keys
                if '.' in score_key:
                    parts = score_key.split('.')
                    value = tool_results[category]
                    for part in parts:
                        value = value.get(part, {})
                    scores[tool] = value if isinstance(value, (int, float)) else 0
                else:
                    scores[tool] = tool_results[category].get(score_key, 0)
    
    # Sort tools by score (higher is better)
    sorted_tools = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Assign ranks
    for i, (tool, score) in enumerate(sorted_tools):
        rankings[tool] = {
            "rank": i + 1,
            "score": score
        }
    
    return rankings


def generate_overall_ranking(rankings):
    """Generate overall ranking based on category rankings"""
    # Initialize overall scores
    overall_scores = {}
    
    # Category weights
    weights = {
        "complexity": 0.15,
        "security": 0.25,
        "deployment": 0.25,
        "performance": 0.2,
        "cost": 0.15
    }
    
    # Calculate weighted scores
    for category, category_rankings in rankings.items():
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
    overall_ranking = {}
    for i, (tool, score) in enumerate(sorted_tools):
        overall_ranking[tool] = {
            "rank": i + 1,
            "score": round(score, 2)
        }
    
    return overall_ranking


def generate_visualizations(report, output_dir):
    """Generate visualization charts for the report"""
    # Create charts directory
    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    # Generate category scores chart
    generate_category_scores_chart(report, charts_dir)
    
    # Generate overall ranking chart
    generate_overall_ranking_chart(report, charts_dir)
    
    # Generate performance comparison chart
    generate_performance_comparison(report, charts_dir)
    
    # Generate cost comparison chart
    generate_cost_comparison(report, charts_dir)


def generate_category_scores_chart(report, charts_dir):
    """Generate a chart comparing tool scores across categories"""
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
    
    # Create chart
    ax = df.plot(kind='bar', figsize=(12, 8), width=0.7)
    
    plt.title('IaC Tools Comparison by Category', fontsize=16)
    plt.xlabel('Category', fontsize=14)
    plt.ylabel('Score (higher is better)', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Tool', fontsize=12)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'category_scores.png'))
    plt.close()


def generate_overall_ranking_chart(report, charts_dir):
    """Generate a chart showing overall ranking"""
    tools = []
    scores = []
    
    for tool, data in sorted(report["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
        tools.append(tool)
        scores.append(data["score"])
    
    # Create chart
    plt.figure(figsize=(10, 6))
    bars = plt.barh(tools, scores, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    
    # Add score labels
    for bar, score in zip(bars, scores):
        plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                 f'{score:.2f}', va='center')
    
    plt.title('Overall IaC Tool Ranking', fontsize=16)
    plt.xlabel('Score (higher is better)', fontsize=14)
    plt.ylabel('Tool', fontsize=14)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'overall_ranking.png'))
    plt.close()


def generate_performance_comparison(report, charts_dir):
    """Generate a chart comparing performance metrics"""
    tools = report["tools_compared"]
    
    # Extract performance metrics
    execution_times = []
    cpu_peaks = []
    memory_peaks = []
    
    for tool in tools:
        if "performance" in report["results"].get(tool, {}):
            perf_data = report["results"][tool]["performance"]
            
            # Extract average execution time for operations
            time_sum = 0
            operation_count = 0
            for op_data in perf_data.get("operations", {}).values():
                time_sum += op_data.get("execution_time", 0)
                operation_count += 1
                
            avg_time = time_sum / max(1, operation_count)
            execution_times.append(avg_time)
            
            # Extract peak CPU and memory
            cpu_peak = 0
            memory_peak = 0
            for op_data in perf_data.get("operations", {}).values():
                cpu_peak = max(cpu_peak, op_data.get("cpu_peak", 0))
                memory_peak = max(memory_peak, op_data.get("memory_peak", 0))
                
            cpu_peaks.append(cpu_peak)
            memory_peaks.append(memory_peak)
        else:
            execution_times.append(0)
            cpu_peaks.append(0)
            memory_peaks.append(0)
    
    # Create grouped bar chart
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
    
    # Execution time chart
    ax1.bar(tools, execution_times, color='skyblue')
    ax1.set_title('Average Operation Execution Time')
    ax1.set_ylabel('Seconds')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # CPU peak chart
    ax2.bar(tools, cpu_peaks, color='lightcoral')
    ax2.set_title('Peak CPU Usage')
    ax2.set_ylabel('CPU %')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Memory peak chart
    ax3.bar(tools, memory_peaks, color='lightgreen')
    ax3.set_title('Peak Memory Usage')
    ax3.set_ylabel('Memory (MB)')
    ax3.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'performance_comparison.png'))
    plt.close()


def generate_cost_comparison(report, charts_dir):
    """Generate a chart comparing cost metrics"""
    tools = report["tools_compared"]
    
    # Extract cost metrics
    monthly_costs = []
    opportunity_counts = []
    
    for tool in tools:
        if "cost" in report["results"].get(tool, {}):
            cost_data = report["results"][tool]["cost"]
            monthly_costs.append(cost_data.get("monthly_cost", 0))
            opportunity_counts.append(len(cost_data.get("cost_optimization_opportunities", [])))
        else:
            monthly_costs.append(0)
            opportunity_counts.append(0)
    
    # Create charts
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # Monthly cost chart
    ax1.bar(tools, monthly_costs, color='skyblue')
    ax1.set_title('Estimated Monthly Cost')
    ax1.set_ylabel('USD ($)')
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Cost optimization opportunities chart
    ax2.bar(tools, opportunity_counts, color='lightcoral')
    ax2.set_title('Cost Optimization Opportunities')
    ax2.set_ylabel('Count')
    ax2.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(os.path.join(charts_dir, 'cost_comparison.png'))
    plt.close()


def generate_html_report(report, output_dir):
    """Generate an HTML report from the report data"""
    # Create HTML report template
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IaC Tools Evaluation Report</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }
            h1, h2, h3 { color: #2c3e50; }
            .container { max-width: 1200px; margin: 0 auto; }
            .summary { background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            .tool-ranking { display: flex; justify-content: space-between; margin-bottom: 20px; }
            .tool-card { flex: 1; background-color: #fff; box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
                        margin: 0 10px; padding: 15px; border-radius: 5px; }
            .tool-card h3 { margin-top: 0; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            .metrics-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
            .metrics-table th, .metrics-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }
            .metrics-table th { background-color: #f8f9fa; }
            .chart-container { margin: 30px 0; text-align: center; }
            .chart-container img { max-width: 100%; height: auto; border: 1px solid #ddd; }
            footer { margin-top: 50px; text-align: center; color: #777; border-top: 1px solid #eee; padding-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Infrastructure as Code (IaC) Tools Evaluation Report</h1>
            <p>Generated at: {generated_at}</p>
            
            <div class="summary">
                <h2>Executive Summary</h2>
                <p>This report compares {tools_list} across five key dimensions: code complexity, security compliance, 
                deployment efficiency, performance, and cost efficiency.</p>
                <h3>Overall Ranking</h3>
                <div class="tool-ranking">
                    {overall_ranking_cards}
                </div>
            </div>
            
            <h2>Detailed Category Comparisons</h2>
            
            <div class="chart-container">
                <h3>Comparison by Category</h3>
                <img src="charts/category_scores.png" alt="Category Scores Comparison">
            </div>
            
            {category_sections}
            
            <div class="chart-container">
                <h3>Performance Metrics Comparison</h3>
                <img src="charts/performance_comparison.png" alt="Performance Metrics Comparison">
            </div>
            
            <div class="chart-container">
                <h3>Cost Comparison</h3>
                <img src="charts/cost_comparison.png" alt="Cost Comparison">
            </div>
            
            <footer>
                <p>IaC Tools Evaluation Framework - Dissertation Project</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    # Generate overall ranking cards
    overall_ranking_cards = ""
    for tool, data in sorted(report["overall_ranking"].items(), key=lambda x: x[1]["rank"]):
        rank = data["rank"]
        score = data["score"]
        
        card = f"""
        <div class="tool-card">
            <h3>{tool.capitalize()} - Rank #{rank}</h3>
            <p><strong>Overall Score:</strong> {score:.2f}</p>
            <p><strong>Key Strengths:</strong> {get_tool_strengths(report, tool)}</p>
        </div>
        """
        overall_ranking_cards += card
    
    # Generate category sections
    category_sections = ""
    for category in report["categories"]:
        section = f"""
        <h3>{category.capitalize()} Analysis</h3>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Tool</th>
                    <th>Rank</th>
                    <th>Score</th>
                    <th>Key Findings</th>
                </tr>
            </thead>
            <tbody>
                {generate_category_table_rows(report, category)}
            </tbody>
        </table>
        """
        category_sections += section
    
    # Fill template
    html_report = html_template.format(
        generated_at=report["generated_at"],
        tools_list=", ".join(tool.capitalize() for tool in report["tools_compared"]),
        overall_ranking_cards=overall_ranking_cards,
        category_sections=category_sections
    )
    
    # Save HTML report
    html_file = os.path.join(output_dir, "report.html")
    with open(html_file, 'w') as f:
        f.write(html_report)
    
    print(f"HTML report saved to: {html_file}")


def get_tool_strengths(report, tool):
    """Identify a tool's strengths based on category rankings"""
    strengths = []
    
    for category, rankings in report["rankings"].items():
        if tool in rankings and rankings[tool]["rank"] == 1:
            strengths.append(f"Best in {category.capitalize()}")
    
    return ", ".join(strengths) if strengths else "Balanced performance"


def generate_category_table_rows(report, category):
    """Generate HTML table rows for a category comparison"""
    rows = ""
    
    if category in report["rankings"]:
        for tool, data in sorted(report["rankings"][category].items(), key=lambda x: x[1]["rank"]):
            rank = data["rank"]
            score = data["score"]
            
            # Extract key findings based on category
            findings = get_category_findings(report, tool, category)
            
            row = f"""
            <tr>
                <td>{tool.capitalize()}</td>
                <td>{rank}</td>
                <td>{score:.2f}</td>
                <td>{findings}</td>
            </tr>
            """
            rows += row
    
    return rows


def get_category_findings(report, tool, category):
    """Extract key findings for a tool in a specific category"""
    findings = []
    
    if tool in report["results"] and category in report["results"][tool]:
        data = report["results"][tool][category]
        
        if category == "complexity":
            findings.append(f"Resource count: {data.get('resource_count', 'N/A')}")
            findings.append(f"Module count: {data.get('module_count', 'N/A')}")
        
        elif category == "security":
            if "overall" in data:
                findings.append(f"Pass rate: {data['overall'].get('pass_percentage', 0):.1f}%")
                findings.append(f"Failed checks: {data['overall'].get('failed', 0)}")
        
        elif category == "deployment":
            if "overall" in data:
                findings.append(f"Deployment time: {data['overall'].get('total_time_seconds', 0):.1f}s")
                findings.append(f"Peak CPU: {data['overall'].get('peak_cpu_percent', 0):.1f}%")
        
        elif category == "performance":
            if "summary" in data:
                fastest = data["summary"].get("fastest_operation", "N/A")
                slowest = data["summary"].get("slowest_operation", "N/A")
                findings.append(f"Fastest op: {fastest}")
                findings.append(f"Slowest op: {slowest}")
        
        elif category == "cost":
            findings.append(f"Monthly cost: ${data.get('monthly_cost', 0):.2f}")
            findings.append(f"Optimization opportunities: {len(data.get('cost_optimization_opportunities', []))}")
    
    return ", ".join(findings) if findings else "No data available"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate final IaC evaluation report")
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