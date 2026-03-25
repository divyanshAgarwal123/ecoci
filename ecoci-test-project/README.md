# EcoCI Test Project

This project has **intentional CI/CD problems** to test the EcoCI optimizer.

## Known Issues (EcoCI should detect all of these)

### CI/CD Pipeline Problems:
1. ❌ No dependency caching - downloads 500MB every run
2. ❌ Heavy Docker images (node:18 instead of node:18-slim)
3. ❌ Sequential job execution (lint/test/build don't use `needs:`)
4. ❌ No test parallelization
5. ❌ Runs on documentation-only changes
6. ❌ Missing security scanning (SAST, Secret Detection, Dependency Scanning)
7. ❌ Hardcoded AWS credentials in deploy script
8. ❌ Dangerous patterns: curl|bash, :latest tags, privileged containers
9. ❌ allow_failure on security jobs

### Code-Level Problems:
10. ❌ N+1 query in getUsers() - should use JOIN
11. ❌ Slow test (generateReport takes 12 seconds)
12. ❌ Memory leak in cache (unbounded growth)
13. ❌ Flaky tests with timing dependencies
14. ❌ Race condition in concurrent test

## Expected EcoCI Output

EcoCI should:
- Calculate current CO₂ emissions
- Detect all 14 problems
- Generate optimized .gitlab-ci.yml with:
  - Caching enabled
  - node:18-slim images
  - Parallel job execution with needs:
  - GitLab security templates
  - Rules to skip doc changes
- Suggest code fixes:
  - Eager loading for N+1 queries
  - Mocking for slow tests
  - LRU cache with size limits
  - Fix flaky tests with proper mocking
- Calculate savings (time, cost, CO₂)
- Create merge request with fixes

## Running Tests

```bash
npm install
npm run test:unit
npm run test:integration
npm run lint
```
