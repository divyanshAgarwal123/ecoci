const { getUsers, generateReport } = require('./index');

// SLOW TEST - Takes 12+ seconds without mocking
describe('Report Generation', () => {
  test('generates report for user', async () => {
    const result = await generateReport(123);
    expect(result.userId).toBe(123);
    expect(result.report).toBeDefined();
  }, 15000); // 15 second timeout
});

// FLAKY TEST - Has timing dependency
describe('Users API', () => {
  test('should return users within reasonable time', async () => {
    const start = Date.now();
    const users = await getUsers();
    const duration = Date.now() - start;
    
    // FLAKY: Fails randomly if DB is slow
    expect(duration).toBeLessThan(100);
    expect(users).toBeInstanceOf(Array);
  });
});

// ANOTHER FLAKY TEST - Race condition
describe('Async operations', () => {
  test('should handle concurrent requests', async () => {
    let counter = 0;
    
    // Race condition
    const promises = [1, 2, 3].map(async () => {
      const temp = counter;
      await new Promise(resolve => setTimeout(resolve, 10));
      counter = temp + 1;
    });
    
    await Promise.all(promises);
    expect(counter).toBe(3); // FLAKY: Sometimes passes, sometimes fails
  });
});
