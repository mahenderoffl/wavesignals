const { Client } = require('pg');

// User's provided connection string
const connectionString = connection string

const client = new Client({ connectionString });

const schema = `
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    tags TEXT,
    image TEXT,
    published BOOLEAN DEFAULT FALSE,
    author TEXT DEFAULT 'WaveSignals',
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    config JSONB DEFAULT '{}'::jsonb
);

-- Insert default settings if not exists
INSERT INTO settings (id, config) 
VALUES (1, '{"ads_enabled": false, "testMode": true}'::jsonb)
ON CONFLICT (id) DO NOTHING;
`;

async function init() {
    try {
        console.log("🔌 Connecting to DB...");
        await client.connect();

        console.log("🛠️ Creating Tables...");
        await client.query(schema);

        console.log("✅ Database Initialized Successfully!");
    } catch (e) {
        console.error("❌ Init Failed:", e);
    } finally {
        await client.end();
    }
}

init();
