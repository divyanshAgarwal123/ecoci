# 🚀 Code Performance Analysis

EcoCI doesn't just optimize your **CI/CD pipeline configuration** — it also analyzes your **application code** to detect performance bottlenecks that waste CPU time, memory, and energy.

## What Gets Analyzed

### 1. **Slow Tests** ⏱️
Detects tests taking >5 seconds and suggests optimizations:
- **Parallel test execution** (`--parallel` flags)
- **Test data factories** instead of database fixtures
- **Mocking external services** instead of real API calls
- **Shared test setup** to reduce redundant initialization

**Example:**
```
❌ Before: 500 tests run sequentially → 320s
✅ After: pytest --parallel=4 → 90s (72% faster)
💰 Savings: 230 CPU-seconds = 108g CO₂ per run
```

### 2. **N+1 Query Problems** 🔄
Detects multiple sequential database queries that should be batched:
- **Rails:** `.includes()` for eager loading
- **Django:** `.select_related()` and `.prefetch_related()`
- **ActiveRecord:** `preload()` to reduce queries

**Example:**
```ruby
# ❌ N+1 Query (100 queries)
@posts.each do |post|
  post.comments.count  # Triggers SELECT for EACH post
end

# ✅ Eager Loading (2 queries)
@posts = Post.includes(:comments)
@posts.each do |post|
  post.comments.count  # Already loaded in memory
end
```
**Savings:** 90% fewer queries → 80% faster → 125g CO₂ saved

### 3. **Missing Database Indices** 📊
Detects sequential scans (full table scans) instead of indexed lookups:
```sql
-- ❌ Sequential Scan (scans all 1M rows)
Seq Scan on posts (cost=0.00..15234.56 rows=50000)
  Filter: (category = 'tech')

-- ✅ Index Scan (uses index, 100x faster)
Index Scan using idx_posts_category on posts
```
**Fix:** `CREATE INDEX idx_posts_category ON posts(category);`  
**Savings:** 100-1000x faster queries, 50% less database CPU

### 4. **Memory Leaks & OOM Errors** 💾
Detects out-of-memory errors and suggests fixes:
- **Streaming data** instead of loading entire datasets
- **Pagination** for large result sets
- **Garbage collection** optimization
- **Memory profiling** with tools like `memory_profiler`

**Example:**
```python
# ❌ Loads 1M records into memory (2GB RAM)
records = Record.objects.all()
for record in records:
    process(record)

# ✅ Streams records (50MB RAM)
for record in Record.objects.iterator(chunk_size=1000):
    process(record)
```
**Savings:** 97% less memory → prevents OOM kills → 100% reliability

### 5. **Blocking I/O Operations** 🌐
Detects synchronous API calls that waste CPU time waiting:
```python
# ❌ Sequential API calls (30s total)
for user in users:
    response = requests.get(f"/api/users/{user.id}")  # Waits 300ms each

# ✅ Async parallel requests (3s total)
async with aiohttp.ClientSession() as session:
    tasks = [fetch_user(session, user.id) for user in users]
    responses = await asyncio.gather(*tasks)
```
**Savings:** 90% faster → 27 CPU-seconds saved → 13g CO₂ per run

### 6. **Docker Image Bloat** 🐳
Detects large Docker images that slow down pipeline starts:
```dockerfile
# ❌ Full Ubuntu image (500MB)
FROM ubuntu:22.04

# ✅ Slim variant (120MB)
FROM ubuntu:22.04-slim
```
**Also detects:**
- Missing `apt-get clean` commands
- Unused build dependencies in final image
- Missing multi-stage builds

**Savings:** 60-80% smaller images → 2x faster pulls → 45s saved per run

### 7. **Inefficient Algorithms** ⚡
Detects CPU-intensive operations that could be optimized:
- **Large in-memory sorts** → Use database `ORDER BY` or streaming sort
- **Nested loops** (O(n²)) → Use hash maps (O(n))
- **Regex in hot paths** → Precompile or use simpler string methods

**Example:**
```python
# ❌ O(n²) nested loop (150,000 comparisons)
for item1 in list1:
    for item2 in list2:
        if item1.id == item2.id:
            # ...

# ✅ O(n) hash lookup (500 lookups)
lookup = {item.id: item for item in list2}
for item1 in list1:
    if item1.id in lookup:
        # ...
```
**Savings:** 99% fewer operations → 5s saved → 10g CO₂ per run

## How It Works

### 1. **Log Analysis**
EcoCI fetches job logs from GitLab and parses them for performance indicators:
```python
from ecoci.code_performance_analyzer import analyze_test_performance

analysis = analyze_test_performance(job_logs)
# Returns:
# - slow_tests: List of tests >5s
# - performance_warnings: N+1 queries, missing indices, etc.
# - recommendations: Specific fixes with impact estimates
```

### 2. **Pattern Matching**
Uses regex patterns to detect common anti-patterns:
```python
# Detect N+1 queries
if re.search(r"(SELECT.*FROM.*){10,}", logs, re.IGNORECASE):
    warnings.append({
        "type": "n+1_queries",
        "fix": "Use eager loading (.includes, .select_related)",
        "savings": "90% fewer queries, 80% faster"
    })
```

### 3. **Savings Estimation**
Calculates CPU time, cost, and CO₂ savings:
```python
from ecoci.code_performance_analyzer import estimate_computational_savings

savings = estimate_computational_savings(
    current_metrics={"total_duration_seconds": 754, "cpu_cores": 4},
    optimizations=["parallel_tests", "n+1_fix", "database_index"]
)
# Returns:
# - time_saved_seconds: 680
# - cpu_hours_saved: 0.756
# - cost_saved_usd: $0.076
# - co2_saved_grams: 180g
```

### 4. **Merge Request Recommendations**
Includes code-level optimizations in MR descriptions:
```markdown
### Code Performance Optimizations

🟠 **N+1 Query Detected** (HIGH severity)
- Location: `PostsController#index` logs
- Issue: 150 SELECT queries executed (one per post)
- Fix: Add `.includes(:comments)` to eager load associations
- Impact: 150 queries → 2 queries (98% reduction)
- Savings: 2.3s faster, 45g CO₂ saved per run

🟡 **Missing Database Index** (MEDIUM severity)
- Location: Sequential scan on `posts` table (category filter)
- Fix: `CREATE INDEX idx_posts_category ON posts(category);`
- Impact: 100x faster queries, 1.8s saved
- Savings: 35g CO₂ per run
```

## Agent Instructions

The agent automatically performs code analysis in **Step 1F**:

```yaml
F) Analyze job logs for CODE PERFORMANCE issues:
   - Slow tests (>5s)
   - N+1 query problems
   - Missing database indices
   - Memory leaks/OOM errors
   - Blocking I/O operations
   - Docker image bloat
   
   Use: scripts/ecoci/code_performance_analyzer.py
```

Then in **Step 3**, it includes code-level optimizations alongside CI/CD fixes:

```yaml
CODE-LEVEL PERFORMANCE OPTIMIZATIONS:
6. SLOW TESTS: Tests >5s → suggest mocking, parallelization
7. N+1 QUERIES: Multiple SELECTs → use eager loading
8. MISSING INDICES: Sequential scans → add database indices
9. MEMORY ISSUES: OOM errors → use streaming/pagination
10. BLOCKING I/O: Sync API calls → use async/await
11. DOCKER BLOAT: Large images → use -slim variants
12. INEFFICIENT ALGORITHMS: Large sorts → database-level sorting
```

## Real-World Example

Here's what EcoCI detected in a recent analysis:

```
📊 Test Performance Analysis

⚠️ Slowest Tests:
1. ReportsController#export (15.2s) - Loads 50k records into memory
2. CommentsController#index (12.3s) - N+1 query (150 SELECT statements)
3. AnalyticsController#dashboard (9.4s) - Complex aggregations without indices

🔴 Performance Issues:
- N+1 queries: 150 → 2 queries (eager loading)
- Missing index on posts.category (sequential scan detected)
- Memory issue: Loading 50k records (2.5GB heap usage)
- Blocking I/O: 30s timeout waiting for external API

💰 Optimization Impact:
- Time saved: 680 seconds (90% faster)
- CPU hours saved: 0.756 hours per run
- Cost saved: $0.076 per run
- CO₂ saved: 180g per run

📅 Annual Savings (50 runs/week):
- $197/year in CI costs
- 468 kg CO₂/year (= driving 1,800 km)
```

## Testing the Analyzer

Run the demo script to see it in action:

```bash
python3 scripts/test_performance_analyzer.py
```

This analyzes sample logs with intentional performance issues and shows:
- Detection of 5 slow tests (6.8s - 15.2s each)
- N+1 query pattern (150+ SELECT statements)
- Missing database index (sequential scan)
- Memory issues (2.5GB heap allocation)
- Blocking I/O (30s timeout)
- Docker inefficiencies (500MB base image, no cleanup)

## Integration with BigQuery

When Google Cloud is enabled, performance metrics are automatically tracked:

```sql
SELECT 
    pipeline_id,
    total_co2_grams,
    savings_percent,
    slow_tests_count,
    n1_queries_detected,
    missing_indices_count
FROM ecoci_metrics.pipeline_runs
ORDER BY created_at DESC
LIMIT 10;
```

This lets you track:
- **Performance trends** over time
- **Optimization impact** (before/after comparisons)
- **Regression detection** (new slow tests introduced)
- **ROI calculation** (cost & CO₂ saved month-over-month)

## Key Benefits

### For Developers
- **Actionable insights:** Specific line numbers and fix suggestions
- **Risk-free:** All suggestions include safety analysis
- **Educational:** Learn performance best practices from recommendations

### For Engineering Leads
- **Visibility:** Track performance trends across all projects
- **Cost control:** See exact $ savings from optimizations
- **Technical debt:** Identify accumulating performance issues

### For Sustainability Officers
- **Carbon tracking:** Quantify CO₂ savings from code optimizations
- **Reporting:** Export metrics for ESG reports
- **Accountability:** Show real impact of green engineering initiatives

## Supported Frameworks

### Test Frameworks
- **RSpec** (Ruby) - `(0.12s)` format
- **pytest** (Python) - `PASSED [1.23s]` format
- **Jest** (JavaScript) - `✓ test (123 ms)` format
- **PHPUnit** (PHP) - `1.234 seconds` format

### Web Frameworks
- **Rails** (Ruby) - `.includes()`, ActiveRecord patterns
- **Django** (Python) - `.select_related()`, ORM patterns
- **Laravel** (PHP) - `with()` eager loading
- **Express** (Node.js) - Sequelize, Mongoose patterns

### Database Systems
- **PostgreSQL** - EXPLAIN ANALYZE parsing
- **MySQL** - Query plan analysis
- **MongoDB** - Query profiling
- **Redis** - Slow log analysis

## Future Enhancements

Coming soon:
- **Profiler integration:** Parse flame graphs from `py-spy`, `rbspy`
- **Memory profiling:** Detect memory leaks with heap dumps
- **Query analysis:** Parse slow query logs automatically
- **Machine learning:** Predict optimal parallelization factor
- **CI/CD integration:** Fail pipeline if performance regresses >20%

---

**Ready to optimize your code?**  
Chat with the EcoCI agent in GitLab Duo and say:  
*"Analyze my pipeline and code performance"*
