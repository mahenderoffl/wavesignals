// Netlify Function: subscribe
// Expects POST with JSON { email }
// Forwards to Buttondown using BUTTONDOWN_API_KEY env var

exports.handler = async function(event, context) {
  if (event.httpMethod !== 'POST') {
    return { statusCode: 405, body: JSON.stringify({ error: 'Method not allowed' }) };
  }

  let body;
  try { body = JSON.parse(event.body || '{}'); } catch (e) { body = {}; }
  const { email } = body;
  if (!email) return { statusCode: 400, body: JSON.stringify({ error: 'missing email' }) };

  const key = process.env.BUTTONDOWN_API_KEY;
  if (!key) return { statusCode: 500, body: JSON.stringify({ error: 'server misconfigured' }) };

  try {
    const resp = await fetch('https://buttondown.email/api/emails', {
      method: 'POST',
      headers: {
        'Authorization': 'Token ' + key,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });

    const json = await resp.json().catch(() => ({}));
    if (!resp.ok) return { statusCode: resp.status, body: JSON.stringify({ error: 'downstream', details: json }) };
    return { statusCode: 200, body: JSON.stringify(json) };
  } catch (err) {
    return { statusCode: 502, body: JSON.stringify({ error: 'proxy error', details: String(err) }) };
  }
};
