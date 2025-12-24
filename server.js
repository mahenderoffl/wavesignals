require('dotenv').config();
const express = require('express');
const fetch = require('node-fetch');
const cors = require('cors');

const app = express();
app.use(express.json());
app.use(cors());

const PORT = process.env.PORT || 3000;

app.post('/api/subscribe', async (req, res) => {
  const email = (req.body && req.body.email) || '';
  if (!email) return res.status(400).json({ error: 'missing email' });

  const key = process.env.BUTTONDOWN_API_KEY;
  if (!key) return res.status(500).json({ error: 'server misconfigured: missing BUTTONDOWN_API_KEY' });

  try {
    const r = await fetch('https://buttondown.email/api/emails', {
      method: 'POST',
      headers: {
        'Authorization': 'Token ' + key,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });

    const data = await r.json().catch(() => ({}));
    if (!r.ok) return res.status(r.status).json({ error: 'downstream', details: data });
    return res.json(data);
  } catch (err) {
    return res.status(502).json({ error: 'proxy error', details: String(err) });
  }
});

app.listen(PORT, () => console.log(`Local API server listening on http://localhost:${PORT}`));
