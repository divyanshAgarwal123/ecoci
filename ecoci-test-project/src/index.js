const express = require('express');
const { Pool } = require('pg');

const app = express();
const port = process.env.PORT || 3000;

// N+1 QUERY PROBLEM - This will be detected by code analyzer
async function getUsers() {
  const pool = new Pool();
  const users = await pool.query('SELECT * FROM users');
  
  // BAD: Makes N separate queries instead of using JOIN
  for (const user of users.rows) {
    const posts = await pool.query('SELECT * FROM posts WHERE user_id = $1', [user.id]);
    user.posts = posts.rows;
  }
  
  return users.rows;
}

// SLOW TEST PROBLEM - This function is slow and not mocked in tests
async function generateReport(userId) {
  // Simulates expensive operation (12 seconds)
  const start = Date.now();
  while (Date.now() - start < 12000) {
    // Blocking operation
  }
  return { userId, report: 'data' };
}

// MEMORY LEAK PROBLEM - Cache never clears
const cache = {};
app.get('/data/:id', async (req, res) => {
  const id = req.params.id;
  
  // Memory leak: cache grows unbounded
  if (!cache[id]) {
    cache[id] = await fetchLargeDataset(id); // 50MB per entry
  }
  
  res.json(cache[id]);
});

app.get('/users', async (req, res) => {
  const users = await getUsers();
  res.json(users);
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});

async function fetchLargeDataset(id) {
  // Simulates fetching large data
  return { id, data: 'x'.repeat(50 * 1024 * 1024) };
}

module.exports = { app, getUsers, generateReport };
