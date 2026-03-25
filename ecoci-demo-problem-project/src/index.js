const express = require('express');

const app = express();

// Simulated in-memory dataset
const users = Array.from({ length: 200 }, (_, i) => ({ id: i + 1, name: `user-${i + 1}` }));
const posts = Array.from({ length: 2000 }, (_, i) => ({ id: i + 1, userId: (i % 200) + 1, title: `post-${i + 1}` }));

// N+1 style pattern (intentionally inefficient)
function getUsersWithPostsSlow() {
  const result = [];
  for (const user of users) {
    const userPosts = posts.filter((p) => p.userId === user.id);
    result.push({ ...user, posts: userPosts });
  }
  return result;
}

// Intentionally blocking CPU work
function generateReport(userId) {
  const start = Date.now();
  while (Date.now() - start < 6000) {
    // busy wait: intentionally bad for demo
  }
  return { userId, report: 'generated' };
}

// Unbounded cache growth
const cache = {};
function getLargePayload(key) {
  if (!cache[key]) {
    cache[key] = { key, blob: 'x'.repeat(2 * 1024 * 1024) };
  }
  return cache[key];
}

app.get('/users', (_req, res) => {
  res.json(getUsersWithPostsSlow());
});

app.get('/report/:id', (req, res) => {
  const id = Number(req.params.id);
  res.json(generateReport(id));
});

app.get('/cache/:key', (req, res) => {
  res.json(getLargePayload(req.params.key));
});

if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    console.log(`Demo app running on ${port}`);
  });
}

module.exports = {
  app,
  getUsersWithPostsSlow,
  generateReport,
  getLargePayload,
};
