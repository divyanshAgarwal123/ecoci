#!/usr/bin/env python3
"""
Test script to demonstrate code performance analysis capabilities.
"""

from ecoci.code_performance_analyzer import (
    analyze_test_performance,
    analyze_docker_performance,
    estimate_computational_savings,
    generate_performance_report
)

# Sample test job logs with various performance issues
SAMPLE_TEST_LOGS = """
Running RSpec tests...

Finished in 12 minutes 34 seconds (files took 2.45 seconds to load)
1250 examples, 0 failures

Examples:
  UserController#create creates a new user (0.12s)
  UserController#update updates user email (0.08s)
  PostsController#index loads all posts (8.45s)
  PostsController#show displays single post (0.15s)
  CommentsController#index N+1 query test (12.30s)
  SearchController#search performs full-text search (6.78s)
  ReportsController#export generates CSV report (15.20s)
  AnalyticsController#dashboard calculates metrics (9.45s)

Database queries:
SELECT * FROM users WHERE id = 1;
SELECT * FROM posts WHERE user_id = 1;
SELECT * FROM comments WHERE post_id = 1;
SELECT * FROM comments WHERE post_id = 2;
SELECT * FROM comments WHERE post_id = 3;
SELECT * FROM comments WHERE post_id = 4;
SELECT * FROM comments WHERE post_id = 5;
SELECT * FROM comments WHERE post_id = 6;
SELECT * FROM comments WHERE post_id = 7;
SELECT * FROM comments WHERE post_id = 8;
SELECT * FROM comments WHERE post_id = 9;
SELECT * FROM comments WHERE post_id = 10;

EXPLAIN ANALYZE:
Seq Scan on posts  (cost=0.00..1234.56 rows=50000 width=256) (actual time=0.234..45.678 rows=50123 loops=1)
  Filter: (category = 'tech')
  Rows Removed by Filter: 25000

Heap memory usage: 2.5 GB
Sorting 150000 records in memory...

External API calls:
Waiting for response from api.example.com... (timeout: 30s)
Connection timeout after 30 seconds
Retrying...
"""

SAMPLE_DOCKERFILE = """
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \\
    python3 \\
    python3-pip \\
    nodejs \\
    npm \\
    postgresql-client \\
    redis-tools

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY package.json .
RUN npm install

COPY . /app
WORKDIR /app

CMD ["python3", "app.py"]
"""


def main():
    print("=" * 70)
    print("🚀 EcoCI Code Performance Analysis Demo")
    print("=" * 70)
    print()
    
    # Analyze test performance
    print("📊 Analyzing test performance...\n")
    test_analysis = analyze_test_performance(SAMPLE_TEST_LOGS)
    
    print(f"✅ Analysis complete!")
    print(f"   - Total test time: {test_analysis['total_test_time']}s")
    print(f"   - Slow tests found: {len(test_analysis['slow_tests'])}")
    print(f"   - Performance warnings: {len(test_analysis['performance_warnings'])}")
    print()
    
    # Show slow tests
    if test_analysis['slow_tests']:
        print("⚠️  Slowest Tests:\n")
        for i, test in enumerate(test_analysis['slow_tests'][:5], 1):
            print(f"   {i}. {test['name'][:60]}")
            print(f"      Duration: {test['duration']}s")
            print(f"      Framework: {test['framework']}")
            print()
    
    # Show performance issues
    if test_analysis['performance_warnings']:
        print("🔴 Performance Issues Detected:\n")
        for warning in test_analysis['performance_warnings']:
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢"
            }
            emoji = severity_emoji.get(warning['severity'], '⚪')
            
            print(f"{emoji} {warning['type'].upper()} ({warning['severity']})")
            print(f"   Issue: {warning['message']}")
            print(f"   Impact: {warning['impact']}")
            print(f"   Fix: {warning['fix']}")
            if 'savings' in warning:
                print(f"   💰 Savings: {warning['savings']}")
            print()
    
    # Analyze Dockerfile
    print("🐳 Analyzing Dockerfile...\n")
    docker_analysis = analyze_docker_performance(SAMPLE_DOCKERFILE)
    
    if docker_analysis['issues']:
        print("Docker Issues Found:\n")
        for issue in docker_analysis['issues']:
            print(f"   - {issue['message']}")
            print(f"     Fix: {issue['fix']}")
            print(f"     Savings: {issue['savings']}")
            print()
    
    # Estimate savings
    print("💰 Estimating Computational Savings...\n")
    current_metrics = {
        "total_duration_seconds": 754,  # 12 min 34 sec
        "cpu_cores": 4
    }
    optimizations = [
        "parallel_tests",
        "n+1_fix",
        "database_index",
        "docker_optimization"
    ]
    
    savings = estimate_computational_savings(current_metrics, optimizations)
    
    print(f"   Current Duration: {current_metrics['total_duration_seconds']}s")
    print(f"   Time Saved: {savings['time_saved_seconds']}s")
    print(f"   Speed Improvement: {savings['percentage_improvement']}%")
    print(f"   CPU Hours Saved: {savings['cpu_hours_saved']} hours")
    print(f"   Cost Saved: ${savings['cost_saved_usd']} per run")
    print(f"   CO₂ Saved: {savings['co2_saved_grams']}g per run")
    print()
    
    print("📋 If you run 50 pipelines/week:")
    print(f"   - Save ${savings['cost_saved_usd'] * 50:.2f} per week")
    print(f"   - Save {savings['co2_saved_grams'] * 50 / 1000:.1f} kg CO₂ per week")
    print(f"   - Save {savings['co2_saved_grams'] * 50 * 52 / 1000:.1f} kg CO₂ per year")
    print()
    
    # Generate full report
    print("=" * 70)
    print("📄 Full Performance Report")
    print("=" * 70)
    print()
    report = generate_performance_report(SAMPLE_TEST_LOGS, SAMPLE_DOCKERFILE)
    print(report)
    
    print("=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print()
    print("The EcoCI agent will now automatically:")
    print("  1. Detect these issues in your pipeline logs")
    print("  2. Suggest specific code-level fixes")
    print("  3. Estimate CPU time & CO₂ savings")
    print("  4. Include recommendations in merge request descriptions")
    print()


if __name__ == "__main__":
    main()
