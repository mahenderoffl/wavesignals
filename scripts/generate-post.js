/**
 * WaveSignals Content Pipeline (v1)
 * Researcher → Strategist → Writer → Quality Gate → Publisher
 */

const fs = require("fs");
const path = require("path");
const qualityGate = require("./quality-gate");

// ===============================
// PATHS
// ===============================
const POSTS_PATH = path.join(__dirname, "../data/posts.json");
const SETTINGS_PATH = path.join(__dirname, "../data/settings.json");
const DRAFTS_PATH = path.join(__dirname, "../data/drafts.json");
const PROMPTS_PATH = path.join(__dirname, "../prompts");

// ===============================
// HELPERS (WERE MISSING — FIXED)
// ===============================
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function stripHtml(html) {
  return html.replace(/<[^>]*>/g, " ");
}

// ===============================
// STEP 1: RESEARCHER
// ===============================
function analyzeHistory(posts) {
  const last10 = posts.slice(0, 10);
  const pillarCount = {};

  last10.forEach(p => {
    const pillar = p.pillar || "unknown";
    pillarCount[pillar] = (pillarCount[pillar] || 0) + 1;
  });

  return {
    lastTopics: last10.map(p => p.title.toLowerCase()),
    pillarCount
  };
}

function runResearcher() {
  const postsData = JSON.parse(fs.readFileSync(POSTS_PATH, "utf-8"));
  const topicsData = JSON.parse(
    fs.readFileSync(path.join(__dirname, "../data/topics.json"), "utf-8")
  );

  const usedTitles = new Set(
    (postsData.posts || []).map(p => p.title.toLowerCase())
  );

  // Build weighted pool
  const pool = [];
  for (const [pillar, config] of Object.entries(topicsData.pillars)) {
    config.topics.forEach(topic => {
      if (!usedTitles.has(topic.toLowerCase())) {
        for (let i = 0; i < config.weight; i++) {
          pool.push({ topic, pillar });
        }
      }
    });
  }

  if (!pool.length) {
    throw new Error("❌ Researcher: No unused topics available");
  }

  const selected = pool[Math.floor(Math.random() * pool.length)];

  return {
    topic: selected.topic,
    pillar: selected.pillar,
    confidence: "high"
  };
}

// ===============================
// STEP 2: STRATEGIST
// ===============================
const FORMATS = {
  CONTRARIAN: { name: "Contrarian Signal", minWords: 700 },
  PATTERN: { name: "Pattern Reveal", minWords: 800 },
  SHIFT: { name: "Silent Shift", minWords: 750 },
  SECOND_ORDER: { name: "Second-Order Effect", minWords: 900 }
};

function runStrategist(research) {
  if (research.pillar === "Career") return FORMATS.CONTRARIAN;
  if (research.pillar === "Money") return FORMATS.PATTERN;
  if (research.pillar === "Tech") return FORMATS.SECOND_ORDER;
  return FORMATS.SHIFT;
}

// ===============================
// STEP 3: WRITER (MANUAL PASTE)
// ===============================
async function runWriter(research, strategy) {
  const writerPrompt = fs.readFileSync(
    path.join(PROMPTS_PATH, "signal-writer.txt"),
    "utf-8"
  );

  console.log("\n📝 PROMPT TO USE:\n");
  console.log(
    writerPrompt
      .replace("{{TOPIC}}", research.topic)
      .replace("{{FORMAT}}", strategy.name)
  );

  console.log("\n⚠️ Paste final HTML content below.\n");

  const aiContent = `
<p>Most people assume growth is about effort. The reality is more uncomfortable.</p>

<p>The system doesn’t reward competence the way we think it does. It rewards visibility, timing, and narrative control.</p>

<p>This is why two equally skilled people end up in very different places.</p>

<p>The real shift happens when you stop optimizing for effort and start optimizing for signal.</p>

<p>Once you see this, you can’t unsee it.</p>
`;

  return aiContent;
}

// ===============================
// STEP 4: PUBLISHER
// ===============================
function publishPost(title, content) {
  const raw = fs.readFileSync(POSTS_PATH, "utf-8");
  const data = JSON.parse(raw);

  const post = {
    id: Date.now(),
    title,
    slug: slugify(title),
    excerpt: stripHtml(content).slice(0, 140),
    content,
    published: true,
    date: new Date().toISOString(),
    image: "/public/og-default.png"
  };

  data.posts.unshift(post);
  fs.writeFileSync(POSTS_PATH, JSON.stringify(data, null, 2));

  console.log("✅ Post published:", title);
}

// ===============================
// PIPELINE RUNNER (FIXED)
// ===============================
async function runPipeline() {
  console.log("🚀 Running WaveSignals pipeline…");

  const researcher = runResearcher();
  const strategist = runStrategist(researcher);
  const content = await runWriter(researcher, strategist);
  const title = researcher.topic;

  // ✅ QUALITY GATE — RUN ONCE, CORRECTLY
  qualityGate({ title, content });

  // Respect automation settings
  let settings = { automation: { enabled: true, manualOnly: false, emergencyStop: false } };
  try {
    settings = JSON.parse(fs.readFileSync(SETTINGS_PATH, 'utf-8')) || settings;
  } catch (e) {
    console.warn('⚠️ settings.json not found or invalid — using defaults');
  }

  const auto = settings.automation || {};
  if (auto.emergencyStop) {
    console.error('⛔ Emergency stop is active — aborting publish.');
    process.exit(2);
  }

  if (!auto.enabled) {
    console.log('⏸ Automation is paused (enabled=false) — not publishing.');
    process.exit(0);
  }

  if (auto.manualOnly) {
    console.log('✋ Manual-publish mode active — saving as draft instead of publishing.');
    // write draft to drafts.json
    try {
      const draftPayload = {
        id: Date.now(),
        title,
        slug: slugify(title),
        excerpt: stripHtml(content).slice(0,140),
        content,
        date: new Date().toISOString()
      };

      let ddata = { drafts: [] };
      try {
        ddata = JSON.parse(fs.readFileSync(DRAFTS_PATH, 'utf-8')) || ddata;
      } catch (e) {
        // create new drafts file
      }
      ddata.drafts.unshift(draftPayload);
      fs.writeFileSync(DRAFTS_PATH, JSON.stringify(ddata, null, 2));
      console.log('🗂 Draft saved to', DRAFTS_PATH);
    } catch (e) {
      console.error('Failed to save draft:', e);
    }

    console.log('📌 Next: review drafts or publish manually via admin');
    process.exit(0);
  }

  // Default: auto-publish
  publishPost(title, content);

  console.log("📌 Next: node scripts/generate-sitemap.js");
}

runPipeline();
