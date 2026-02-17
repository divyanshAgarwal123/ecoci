#!/usr/bin/env python3
"""
Demo: Show cost analysis and production impact prediction.
"""

from ecoci.cost_analyzer import (
    calculate_pipeline_cost,
    calculate_monthly_spending,
    calculate_roi,
    compare_with_industry_benchmarks,
    generate_cost_report
)

from ecoci.production_impact_predictor import (
    predict_n1_impact,
    predict_memory_leak_impact,
    predict_api_timeout_risk,
    generate_production_impact_report
)


def main():
    print("=" * 70)
    print("💰 EcoCI Cost Analysis & Production Impact Demo")
    print("=" * 70)
    print()
    
    # Sample pipeline data
    current_pipeline = {
        "duration": 754,  # seconds
        "jobs": [
            {"name": "build", "duration": 180, "runner": {"tags": ["saas-linux-medium-amd64"]}},
            {"name": "test", "duration": 320, "runner": {"tags": ["saas-linux-medium-amd64"]}},
            {"name": "lint", "duration": 45, "runner": {"tags": ["saas-linux-small-amd64"]}},
            {"name": "deploy", "duration": 90, "runner": {"tags": ["saas-linux-small-amd64"]}},
        ]
    }
    
    optimized_pipeline = {
        "duration": 95,  # After optimization
        "jobs": [
            {"name": "build", "duration": 60, "runner": {"tags": ["saas-linux-medium-amd64"]}},
            {"name": "test", "duration": 95, "runner": {"tags": ["saas-linux-medium-amd64"]}},  # Parallel
            {"name": "lint", "duration": 20, "runner": {"tags": ["saas-linux-small-amd64"]}},
            {"name": "deploy", "duration": 40, "runner": {"tags": ["saas-linux-small-amd64"]}},
        ]
    }
    
    # Cost analysis
    print("📊 COST ANALYSIS\n")
    print("-" * 70)
    
    current_cost = calculate_pipeline_cost(current_pipeline["jobs"])
    print(f"Current pipeline cost: ${current_cost['total_cost']:.2f}")
    
    optimized_cost = calculate_pipeline_cost(optimized_pipeline["jobs"])
    print(f"Optimized pipeline cost: ${optimized_cost['total_cost']:.2f}")
    print(f"Savings per run: ${current_cost['total_cost'] - optimized_cost['total_cost']:.2f}")
    print()
    
    # Monthly spending
    monthly = calculate_monthly_spending(current_cost['total_cost'], 10, 22)  # 10 pipelines/day
    print(f"📅 Current monthly spending (@ 50 runs/week):")
    print(f"   Daily: ${monthly['daily_cost']:.2f}")
    print(f"   Monthly: ${monthly['monthly_cost']:.2f}")
    print(f"   Annual: ${monthly['annual_cost']:.2f}")
    print()
    
    # ROI calculation
    print("💹 ROI CALCULATION\n")
    print("-" * 70)
    
    roi = calculate_roi(
        current_cost['total_cost'],
        optimized_cost['total_cost'],
        current_pipeline['duration'] / 60,
        optimized_pipeline['duration'] / 60,
        team_size=10,
        developer_level="mid",
        pipelines_per_week=50
    )
    
    print(f"Runner cost savings:     ${roi['runner_cost_savings']['annual']:.2f}/year")
    print(f"Productivity gains:      ${roi['developer_productivity_gains']['value_annual']:.2f}/year")
    print(f"Total annual value:      ${roi['total_annual_value']:.2f}")
    print()
    print(f"Implementation cost:     ${roi['implementation_cost']:.2f} (one-time)")
    print(f"Payback period:          {roi['payback_period_weeks']:.1f} weeks")
    print(f"ROI:                     {roi['roi_percentage']:.0f}%")
    print()
    print(f"✅ Saves {roi['developer_productivity_gains']['hours_saved_per_week']:.1f} hours/week for team of 10")
    print()
    
    # Industry benchmark
    print("📈 INDUSTRY BENCHMARK COMPARISON\n")
    print("-" * 70)
    
    benchmark = compare_with_industry_benchmarks(current_pipeline['duration'] / 60, "web_app")
    print(f"Your pipeline:       {benchmark['your_duration_min']:.1f} minutes")
    print(f"Industry median:     {benchmark['benchmark_p50']} minutes")
    print(f"Industry p90:        {benchmark['benchmark_p90']} minutes")
    print(f"Your percentile:     {benchmark['percentile']}")
    print(f"Status:              {benchmark['status'].upper()}")
    print()
    print(f"💡 {benchmark['recommendation']}")
    print()
    print()
    
    # Production impact prediction
    print("🚨 PRODUCTION IMPACT PREDICTION\n")
    print("=" * 70)
    print()
    
    # Simulate detected performance issues
    performance_issues = [
        {
            "type": "n+1_queries",
            "queries_count": 150,
            "location": "PostsController#index"
        },
        {
            "type": "slow_query",
            "query_time_seconds": 2.3,
            "location": "posts WHERE category = ?"
        },
        {
            "type": "memory_leak",
            "memory_mb": 10,
            "location": "ReportsController#export"
        },
        {
            "type": "api_timeout",
            "duration_seconds": 8,
            "calls_count": 5,
            "location": "UsersController#sync_external"
        }
    ]
    
    # N+1 prediction
    print("🔄 N+1 QUERY IMPACT (@ 100 req/s traffic):")
    n1_pred = predict_n1_impact(150, 5.0, 100)
    print(f"   Severity: {n1_pred['severity'].upper()}")
    print(f"   Latency per request: {n1_pred['latency_per_request_ms']:.0f}ms")
    print(f"   DB queries/second: {n1_pred['db_queries_per_second']:,}")
    print(f"   Impact: {n1_pred['impact_description']}")
    if n1_pred['pool_warning']:
        print(f"   {n1_pred['pool_warning']}")
    print()
    
    # Memory leak prediction
    print("💾 MEMORY LEAK IMPACT (@ 10k req/hour, 4GB server):")
    mem_pred = predict_memory_leak_impact(10, 10000, 4)
    print(f"   Severity: {mem_pred['severity'].upper()}")
    print(f"   Memory leaked: {mem_pred['memory_leaked_per_hour_mb']:.0f}MB/hour")
    print(f"   Time until OOM: {mem_pred['hours_until_oom']:.1f} hours")
    print(f"   Impact: {mem_pred['impact_description']}")
    print(f"   Action: {mem_pred['recommendation']}")
    print()
    
    # API timeout prediction
    print("🌐 API TIMEOUT RISK (5 external calls, 8s each):")
    api_pred = predict_api_timeout_risk(8, 5, 30)
    print(f"   Severity: {api_pred['severity'].upper()}")
    print(f"   Current duration: {api_pred['current_duration_seconds']:.0f}s (sequential)")
    print(f"   If parallel: {api_pred['if_parallel_duration_seconds']:.0f}s")
    print(f"   Time saved: {api_pred['time_saved_by_parallelizing_seconds']:.0f}s")
    print(f"   Will timeout: {'YES' if api_pred['will_timeout'] else 'NO'}")
    print(f"   Fix: {api_pred['recommendation']}")
    print()
    
    print("=" * 70)
    print()
    
    # Full report
    print("📄 FULL COST REPORT")
    print("=" * 70)
    print()
    report = generate_cost_report(
        current_pipeline,
        optimized_pipeline,
        team_size=10,
        pipelines_per_week=50
    )
    print(report)
    
    print()
    print("=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print()
    print("🎯 Key Takeaways:")
    print(f"   1. You're spending ${monthly['annual_cost']:.2f}/year on CI/CD")
    print(f"   2. Your pipeline is {benchmark['slowness_factor']:.1f}x slower than median")
    print(f"   3. N+1 query will add {n1_pred['latency_per_request_ms']:.0f}ms to EVERY request in production")
    print(f"   4. Memory leak will crash server in {mem_pred['hours_until_oom']:.1f} hours")
    print(f"   5. Optimization saves ${roi['total_annual_value']:.2f}/year with {roi['payback_period_weeks']:.1f} week payback")
    print()
    print("💡 These are the metrics developers ACTUALLY care about!")
    print()


if __name__ == "__main__":
    main()
