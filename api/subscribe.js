// Vercel / Serverless API route
// POST { email } -> proxy to Buttondown with BUTTONDOWN_API_KEY env var

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  const { email } = req.body || {};
  if (!email) return res.status(400).json({ error: 'missing email' });

  const key = process.env.BUTTONDOWN_API_KEY;
  if (!key) return res.status(500).json({ error: 'server misconfigured' });

  try {
    const r = await fetch('https://buttondown.email/api/emails', {
      method: 'POST',
      headers: { 'Authorization': 'Token ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) return res.status(r.status).json({ error: 'downstream', details: data });
    return res.status(200).json(data);
  } catch (err) {
    return res.status(502).json({ error: 'proxy error', details: String(err) });
  }
}
