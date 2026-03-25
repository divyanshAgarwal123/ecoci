# EcoCI Demo Problem Project

This project is intentionally designed with CI/CD and code quality issues so EcoCI can detect, analyze, and optimize them in a demo.

## Intentional CI/CD Issues

1. Uses heavy `:latest` Docker images
2. No dependency caching
3. Sequential jobs without effective `needs:` DAG optimization
4. Jobs run even for docs-only changes
5. Expensive runner tags on lightweight jobs
6. Security anti-patterns (`curl | bash`, privileged Docker)
7. Weak/unsafe variable usage patterns in pipeline config
8. Missing timeout protections

## Intentional Application/Test Issues

1. Simulated N+1 query pattern
2. Blocking CPU operation (`generateReport`) for slow tests
3. In-memory unbounded cache behavior
4. Flaky timing-based assertion
5. Race condition style test

## Demo Goal

Use EcoCI to:

- analyze this repository,
- report speed/cost/carbon/security issues,
- suggest and/or generate optimizations,
- and create an MR showing before/after improvements.
