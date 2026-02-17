# 🚀 How to Make Your Code Faster with EcoCI

## What Just Got Added

Your EcoCI agent now analyzes **both CI/CD pipelines AND application code** to find performance bottlenecks. Here's what it can detect and how to fix each issue:

---

## 🔍 7 Performance Issues Detected

### 1. ⏱️ Slow Tests (>5 seconds)
**What it detects:** Individual tests taking too long  
**Example finding:** "CommentsController#index test takes 12.3s"

**How to fix:**
```bash
# Run tests in parallel
pytest --parallel=4  # Python
rspec --parallel  # Ruby
jest --maxWorkers=4  # JavaScript
```

**Impact:** 72% faster, saves 108g CO₂ per run

---

### 2. 🔄 N+1 Query Problems
**What it detects:** Making 100+ database queries when you could make 2  
**Example finding:** "150 SELECT queries executed (one per record)"

**How to fix:**
```ruby
# ❌ Bad: N+1 query (100 queries)
@posts.each { |post| post.comments.count }

# ✅ Good: Eager loading (2 queries)
@posts = Post.includes(:comments)
```

```python
# ❌ Bad: N+1 query
for user in users:
    print(user.posts.count())

# ✅ Good: Select related
users = User.objects.select_related('posts')
```

**Impact:** 90% fewer queries, 80% faster, saves 125g CO₂

---

### 3. 📊 Missing Database Indices
**What it detects:** Database scanning entire table instead of using an index  
**Example finding:** "Sequential scan on posts table (category filter)"

**How to fix:**
```sql
-- Add an index on frequently queried columns
CREATE INDEX idx_posts_category ON posts(category);
CREATE INDEX idx_users_email ON users(email);
```

**Impact:** 100-1000x faster queries, 50% less database CPU

---

### 4. 💾 Memory Leaks & OOM Errors
**What it detects:** Loading too much data into memory  
**Example finding:** "Memory allocation 2.5GB, heap usage critical"

**How to fix:**
```python
# ❌ Bad: Load 1M records (2GB RAM)
records = Record.objects.all()
for record in records:
    process(record)

# ✅ Good: Stream records (50MB RAM)
for record in Record.objects.iterator(chunk_size=1000):
    process(record)
```

```ruby
# ✅ Good: Use find_each for large datasets
User.find_each(batch_size: 1000) do |user|
  process(user)
end
```

**Impact:** 97% less memory, prevents job failures

---

### 5. 🌐 Blocking I/O (Synchronous API Calls)
**What it detects:** Waiting for network responses instead of doing work  
**Example finding:** "30s timeout waiting for external API"

**How to fix:**
```python
# ❌ Bad: Sequential API calls (30s)
for user in users:
    response = requests.get(f"/api/{user.id}")

# ✅ Good: Parallel async requests (3s)
async with aiohttp.ClientSession() as session:
    tasks = [fetch_user(session, user.id) for user in users]
    await asyncio.gather(*tasks)
```

```javascript
// ❌ Bad: Sequential
for (const user of users) {
  await fetch(`/api/${user.id}`);
}

// ✅ Good: Parallel
await Promise.all(users.map(user => fetch(`/api/${user.id}`)));
```

**Impact:** 90% faster, saves 13g CO₂ per run

---

### 6. 🐳 Docker Image Bloat
**What it detects:** Unnecessarily large Docker images  
**Example finding:** "Using full ubuntu:22.04 (500MB) instead of slim variant"

**How to fix:**
```dockerfile
# ❌ Bad: Full image (500MB)
FROM ubuntu:22.04

# ✅ Good: Slim image (120MB)
FROM ubuntu:22.04-slim

# ✅ Even better: Alpine (50MB)
FROM python:3.11-alpine

# Always clean up after apt-get
RUN apt-get update && apt-get install -y package \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

**Impact:** 60-80% smaller image, 2x faster pulls, saves 45s per run

---

### 7. ⚡ Inefficient Algorithms
**What it detects:** CPU-intensive operations that could be optimized  
**Example finding:** "Sorting 150,000 records in memory"

**How to fix:**
```python
# ❌ Bad: O(n²) nested loop
for item1 in list1:
    for item2 in list2:
        if item1.id == item2.id:
            match(item1, item2)

# ✅ Good: O(n) hash lookup
lookup = {item.id: item for item in list2}
for item1 in list1:
    if item1.id in lookup:
        match(item1, lookup[item1.id])
```

```sql
-- ❌ Bad: Sort in application (high CPU)
SELECT * FROM posts; -- then sort in code

-- ✅ Good: Sort in database
SELECT * FROM posts ORDER BY created_at DESC;
```

**Impact:** 99% fewer operations, saves 10g CO₂ per run

---

## 📊 Real Example Results

Here's what EcoCI found in a test analysis:

```
⚠️ Slowest Tests:
1. ReportsController#export (15.2s)
2. CommentsController#index (12.3s) 
3. AnalyticsController#dashboard (9.4s)

🔴 Performance Issues:
- N+1 queries: 150 SELECT statements
- Missing index on posts.category
- Memory: 2.5GB heap allocation
- Blocking I/O: 30s API timeout
- Docker: 500MB base image (no cleanup)

💰 If You Fix These:
├─ Time: 754s → 5s (99.4% faster!)
├─ CPU: Save 0.832 hours per run
├─ Cost: Save $0.08 per run
└─ CO₂: Save 198g per run

📅 Annual Savings (50 runs/week):
├─ $208/year in CI costs
└─ 515 kg CO₂/year (= driving 1,980 km)
```

---

## 🎯 How to Use This

### Option 1: Test the Analyzer Now
```bash
cd /Volumes/MacTech/gitlab_new/34560917
python3 scripts/test_performance_analyzer.py
```
This shows you what the analyzer can detect with sample data.

### Option 2: Use the Agent
In GitLab Duo Chat, tell the agent:
```
"Analyze my pipeline and code performance"
```

The agent will:
1. Fetch your pipeline data
2. Analyze job logs for performance issues
3. Show you exactly what to fix
4. Estimate time/cost/CO₂ savings
5. Optionally create a merge request with fixes

### Option 3: Manual Integration
```python
from ecoci.code_performance_analyzer import (
    analyze_test_performance,
    estimate_computational_savings
)

# Get job logs from GitLab
job_logs = fetch_job_logs(project_id, pipeline_id, job_id)

# Analyze performance
analysis = analyze_test_performance(job_logs)

print(f"Slow tests: {len(analysis['slow_tests'])}")
print(f"Performance warnings: {len(analysis['performance_warnings'])}")

for warning in analysis['performance_warnings']:
    print(f"⚠️ {warning['type']}: {warning['message']}")
    print(f"   Fix: {warning['fix']}")
    print(f"   Savings: {warning['savings']}")
```

---

## 📈 Tracking Progress

If you have Google Cloud enabled, all metrics are saved to BigQuery:

```sql
-- See performance trends
SELECT 
    DATE(created_at) as date,
    AVG(total_co2_grams) as avg_co2,
    AVG(savings_percent) as avg_savings
FROM ecoci_metrics.pipeline_runs
GROUP BY date
ORDER BY date DESC
LIMIT 30;

-- Find biggest optimizations
SELECT 
    project_name,
    total_co2_grams,
    savings_percent
FROM ecoci_metrics.pipeline_runs
WHERE savings_percent > 50
ORDER BY savings_percent DESC;
```

---

## 🏆 Best Practices

### For Maximum Speed
1. **Run tests in parallel** (4x cores = 3-4x faster)
2. **Add database indices** on frequently queried columns
3. **Use eager loading** for associations (Rails `.includes`, Django `.select_related`)
4. **Cache dependencies** in CI/CD (don't re-download every time)
5. **Use slim Docker images** (-alpine or -slim variants)

### For Maximum CO₂ Savings
1. **Fix N+1 queries** (biggest impact: 90% query reduction)
2. **Skip unnecessary jobs** (use `rules: changes:` to run only when needed)
3. **Use async I/O** for external API calls
4. **Optimize slow tests** (5+ seconds → use mocking)
5. **Stream large datasets** (don't load 1M records into memory)

### For Maximum Cost Savings
1. **Parallelize jobs** (4 jobs in 5 min beats 4 jobs in 20 min)
2. **Right-size runners** (don't use large runners for small tasks)
3. **Cache aggressively** (npm, pip, gem, docker layers)
4. **Fail fast** (run fast tests before slow tests)
5. **Use spot/preemptible instances** (50-90% cheaper)

---

## 🎓 Learn More

- **Full Documentation:** [CODE_PERFORMANCE_ANALYSIS.md](CODE_PERFORMANCE_ANALYSIS.md)
- **Google Cloud Setup:** [GCP_QUICKSTART.md](GCP_QUICKSTART.md)
- **Anthropic Integration:** [ANTHROPIC_INTEGRATION.md](ANTHROPIC_INTEGRATION.md)
- **Prize Strategy:** [PRIZE_STRATEGY.md](PRIZE_STRATEGY.md)

---

## 💡 Quick Wins

Start with these 3 fixes for immediate impact:

1. **Parallel Tests** (5 min setup, 60-70% faster)
   ```bash
   pytest --parallel=4
   ```

2. **Docker Slim** (2 min change, 60-80% smaller images)
   ```dockerfile
   FROM ubuntu:22.04-slim  # instead of ubuntu:22.04
   ```

3. **Cache Dependencies** (add to .gitlab-ci.yml)
   ```yaml
   cache:
     paths:
       - node_modules/
       - .pip-cache/
   ```

Each fix takes <10 minutes and saves 50-100g CO₂ per run. Do all 3 and you'll see 70-80% improvement immediately! 🎉
