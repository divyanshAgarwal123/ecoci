const { generateReport, getUsersWithPostsSlow } = require('./index');

describe('Performance problem demos', () => {
  test('slow report generation (intentional)', () => {
    const result = generateReport(101);
    expect(result.userId).toBe(101);
  }, 10000);

  test('N+1 style function returns data', () => {
    const all = getUsersWithPostsSlow();
    expect(all.length).toBeGreaterThan(100);
    expect(Array.isArray(all[0].posts)).toBe(true);
  });
});

describe('Flaky/race behavior demos', () => {
  test('timing-based flaky assertion', async () => {
    const start = Date.now();
    await new Promise((resolve) => setTimeout(resolve, 80));
    const duration = Date.now() - start;
    expect(duration).toBeLessThan(90);
  });

  test('race condition style counter update', async () => {
    let counter = 0;

    const jobs = [1, 2, 3, 4].map(async () => {
      const before = counter;
      await new Promise((resolve) => setTimeout(resolve, 5));
      counter = before + 1;
    });

    await Promise.all(jobs);
    expect(counter).toBe(4);
  });
});
