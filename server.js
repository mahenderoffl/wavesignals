require('dotenv').config();
const express = require('express');
const fetch = require('node-fetch');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 3000;
const DATA_FILE = path.join(__dirname, 'data', 'posts.json');

// --- STATIC FILE SERVING (For Preview) ---
app.use(express.static(path.join(__dirname)));

// --- HELPER: Read/Write Data ---
async function getPosts() {
  try {
    const data = await fs.readFile(DATA_FILE, 'utf8');
    return JSON.parse(data);
  } catch (err) {
    // If file missing, return empty structure
    return { posts: [] };
  }
}

async function savePosts(data) {
  await fs.writeFile(DATA_FILE, JSON.stringify(data, null, 2), 'utf8');
}

// --- API: POSTS (The Core Data Layer) ---

// GET /api/posts - Retrieve all posts
app.get('/api/posts', async (req, res) => {
  try {
    const data = await getPosts();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to read posts' });
  }
});

// POST /api/posts - Create or Update a post
app.post('/api/posts', async (req, res) => {
  try {
    const { post } = req.body;
    if (!post || !post.title) {
      return res.status(400).json({ error: 'Invalid post data' });
    }

    const data = await getPosts();
    const existingIndex = data.posts.findIndex(p => p.id === post.id);

    if (existingIndex >= 0) {
      // Update existing
      data.posts[existingIndex] = { ...data.posts[existingIndex], ...post };
    } else {
      // Create new
      data.posts.unshift(post);
    }

    await savePosts(data);
    console.log(`[SERVER] Saved post: ${post.title}`);
    res.json({ success: true, post });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to save post' });
  }
});

// DELETE /api/posts/:id - Delete a post
app.delete('/api/posts/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const data = await getPosts();
    const initialLength = data.posts.length;
    // Filter out the post with the matching ID
    data.posts = data.posts.filter(p => String(p.id) !== String(id));

    if (data.posts.length !== initialLength) {
      await savePosts(data);
      console.log(`[SERVER] Deleted post: ${id}`);
      res.json({ success: true });
    } else {
      res.status(404).json({ error: 'Post not found' });
    }
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to delete post' });
  }
});

// --- API: SUBSCRIPTIONS (Buttondown) ---
// --- ADS ENDPOINT ---
app.get('/api/ads', (req, res) => {
  res.sendFile(path.join(__dirname, 'data', 'ads.json'));
});

app.post('/api/ads', async (req, res) => {
  try {
    const filePath = path.join(__dirname, 'data', 'ads.json');
    await fs.promises.writeFile(filePath, JSON.stringify(req.body, null, 2));
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'failed to save ads' });
  }
});

// --- API: SUBSCRIBERS (Local JSON) ---
const SUB_FILE = path.join(__dirname, 'data', 'subscribers.json');

// GET /api/subscribers
app.get('/api/subscribers', async (req, res) => {
  try {
    const data = await fs.readFile(SUB_FILE, 'utf8').catch(() => '[]');
    res.json(JSON.parse(data));
  } catch (e) { res.json([]); }
});

// POST /api/subscribe
app.post('/api/subscribe', async (req, res) => {
  const email = (req.body && req.body.email) || '';
  if (!email || !email.includes('@')) return res.status(400).json({ error: 'Invalid email' });

  try {
    let subs = [];
    try {
      const existing = await fs.readFile(SUB_FILE, 'utf8');
      subs = JSON.parse(existing);
    } catch (e) { subs = []; }

    // Deduplicate
    if (!subs.find(s => s.email === email)) {
      subs.push({ email, date: new Date().toISOString() });
      await fs.writeFile(SUB_FILE, JSON.stringify(subs, null, 2));
      console.log(`[SERVER] New Subscriber: ${email}`);
    }

    res.json({ success: true, count: subs.length });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to save subscription' });
  }
});

app.listen(PORT, () => console.log(`API server listening on http://localhost:${PORT}`));
