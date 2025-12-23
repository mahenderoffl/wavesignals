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
  const data = JSON.parse(fs.readFileSync(POSTS_PATH, "utf-8"));
  const history = analyzeHistory(data.posts || []);

  const topicPool = [
    { topic: "Why career growth now depends on visibility, not skill", pillar: "Career" },
    { topic: "The hidden incentive behind hustle culture", pillar: "Money" },
    { topic: "Why most AI products won’t survive 18 months", pillar: "Tech" },
    { topic: "Why people confuse comfort with stability", pillar: "Behavior" }
  ];

  const available = topicPool.filter(
    t => !history.lastTopics.includes(t.topic.toLowerCase())
  );

  if (!available.length) {
    throw new Error("❌ Researcher: No fresh topics available");
  }

  available.sort((a, b) => {
    const aCount = history.pillarCount[a.pillar] || 0;
    const bCount = history.pillarCount[b.pillar] || 0;
    return aCount - bCount;
  });

  return {
    topic: available[0].topic,
    pillar: available[0].pillar
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

  publishPost(title, content);

  console.log("📌 Next: node scripts/generate-sitemap.js");
}

runPipeline();
