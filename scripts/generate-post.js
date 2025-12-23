/**
 * WaveSignals Content Pipeline (v1)
 * Researcher → Strategist → Writer → Publisher
 * PASS 2: Quality Gate Enabled
 */

const fs = require("fs");
const path = require("path");

// Paths
const POSTS_PATH = path.join(__dirname, "../data/posts.json");
const PROMPTS_PATH = path.join(__dirname, "../prompts");

// ===============================
// UTILITIES
// ===============================
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

function stripHtml(html) {
  return html.replace(/<[^>]+>/g, "");
}

function wordCount(text) {
  return stripHtml(text).trim().split(/\s+/).length;
}

// ===============================
// QUALITY GATE (PASS 2)
// ===============================
// ===============================
// PASS 2: QUALITY GATE
// ===============================
function qualityGate(title, content) {
  const plainText = content.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  const words = plainText.split(" ");

  // ❌ Placeholder detection
  const forbidden = [
    "PASTE AI",
    "PLACEHOLDER",
    "GENERATED",
    "TODO",
    "Lorem ipsum"
  ];

  for (const term of forbidden) {
    if (plainText.toLowerCase().includes(term.toLowerCase())) {
      throw new Error(`❌ QUALITY FAIL: Placeholder detected → "${term}"`);
    }
  }

  // ❌ Minimum word count
  if (words.length < 600) {
    throw new Error(`❌ QUALITY FAIL: Word count ${words.length} < 600`);
  }

  // ❌ Hook check (first paragraph must be strong)
  const firstParagraph = plainText.split(".")[0];
  if (firstParagraph.length < 80) {
    throw new Error("❌ QUALITY FAIL: Weak or missing hook paragraph");
  }

  // ❌ Duplicate title
  const raw = fs.readFileSync(POSTS_PATH, "utf-8");
  const existing = JSON.parse(raw).posts || [];

  const duplicate = existing.find(
    p => p.title.toLowerCase() === title.toLowerCase()
  );

  if (duplicate) {
    throw new Error("❌ QUALITY FAIL: Duplicate title detected");
  }

  console.log("✅ Quality gate passed");
}

// ===============================
// STEP 1: SIGNAL RESEARCHER
// ===============================
// ===============================
// STEP 1: SIGNAL RESEARCHER (v1)
// Strategy-aware, offline-first
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

  // choose pillar least used recently
  available.sort((a, b) => {
    const aCount = history.pillarCount[a.pillar] || 0;
    const bCount = history.pillarCount[b.pillar] || 0;
    return aCount - bCount;
  });

  const selected = available[0];

  return {
    topic: selected.topic,
    pillar: selected.pillar,
    confidence: "high"
  };
}

// ===============================
// STEP 2: SIGNAL STRATEGIST
// ===============================
// ===============================
// STRATEGIST — FORMAT DEFINITIONS
// ===============================
const FORMATS = {
  CONTRARIAN: {
    name: "Contrarian Signal",
    hookStyle: "belief-break",
    minWords: 700,
    monetization: "soft"
  },
  PATTERN: {
    name: "Pattern Reveal",
    hookStyle: "pattern",
    minWords: 800,
    monetization: "none"
  },
  SHIFT: {
    name: "Silent Shift",
    hookStyle: "before-after",
    minWords: 750,
    monetization: "soft"
  },
  SECOND_ORDER: {
    name: "Second-Order Effect",
    hookStyle: "unexpected-consequence",
    minWords: 900,
    monetization: "none"
  }
};

function runStrategist(research) {
  // Rotate formats based on pillar
  let selected;

  switch (research.pillar) {
    case "Career":
      selected = FORMATS.CONTRARIAN;
      break;
    case "Money":
      selected = FORMATS.PATTERN;
      break;
    case "Tech":
      selected = FORMATS.SECOND_ORDER;
      break;
    default:
      selected = FORMATS.SHIFT;
  }

  return {
    format: selected.name,
    hookStyle: selected.hookStyle,
    minWords: selected.minWords,
    monetization: selected.monetization,
    rationale: `Chosen based on pillar: ${research.pillar}`
  };
}

// ===============================
// STEP 3: SIGNAL WRITER (MANUAL AI)
// ===============================
// ===============================
// WRITER GUARD — VOICE & STRUCTURE
// ===============================
function writerGuard(content) {
  const plain = content.replace(/<[^>]+>/g, " ").toLowerCase();

  // ❌ Block guide/tutorial language
  const bannedPatterns = [
    "step 1",
    "step-by-step",
    "how to",
    "tips",
    "checklist",
    "guide",
    "best way to",
    "you should",
    "follow these"
  ];

  for (const phrase of bannedPatterns) {
    if (plain.includes(phrase)) {
      throw new Error(`❌ WRITER FAIL: Guide-like language detected → "${phrase}"`);
    }
  }

  // ✅ Require insight markers
  const requiredSignals = [
    "most people",
    "the real reason",
    "what's actually happening",
    "this is why",
    "the problem is not"
  ];

  const hasSignal = requiredSignals.some(s => plain.includes(s));
  if (!hasSignal) {
    throw new Error("❌ WRITER FAIL: Missing insight-driven language");
  }

  console.log("✅ Writer guard passed");
}

async function runWriter(research, strategy) {
  const writerPrompt = fs.readFileSync(
    path.join(PROMPTS_PATH, "signal-writer.txt"),
    "utf-8"
  );

  const finalPrompt = writerPrompt
    .replace("{{TOPIC}}", research.topic)
    .replace("{{FORMAT}}", strategy.format);

  console.log("📝 Writer prompt ready.");
  console.log("------ PROMPT START ------");
  console.log(finalPrompt);
  console.log("------ PROMPT END ------");
  console.log(
    "\n⚠️ Generate content manually and paste the FINAL HTML below.\n"
  );

  // ⬇️ MANUAL PASTE ZONE (REQUIRED)
  const aiContent = `
<p>${strategy.hook}</p>

<p>Most people assume this because it sounds logical. But that assumption hides what’s actually happening beneath the surface.</p>

<p>This is where the pattern becomes visible. When you look closely, you see that the system rewards something entirely different than effort or skill.</p>

<p>The people who benefit from this rarely talk about it openly. Not because it’s secret — but because explaining it breaks the illusion.</p>

<p>This shift matters now more than ever, because the gap between perception and reality is widening.</p>

<p>Once you see this clearly, you start making different decisions — not louder ones.</p>
`;

  return aiContent;
}

// ===============================
// STEP 4: PUBLISHER (QUALITY-GATED)
// ===============================
function publishPost(title, content) {
  // Publishing assumes `qualityGate` was already run by the pipeline.

  const raw = fs.readFileSync(POSTS_PATH, "utf-8");
  const data = JSON.parse(raw);

  const duplicate = data.posts.some(p => p.title === title);
  if (duplicate) {
    console.log("⛔ Duplicate title blocked:", title);
    return;
  }

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

  console.log("✅ High-quality post published:", post.title);
}

// ===============================
// PIPELINE RUNNER
// ===============================
function strategistGuard(strategy, content) {
  const text = content.replace(/<[^>]+>/g, " ");
  const words = text.split(/\s+/).length;

  if (words < strategy.minWords) {
    throw new Error(
      `❌ STRATEGIST FAIL: ${words} words < required ${strategy.minWords}`
    );
  }

  console.log("✅ Strategist guard passed");
}
// ===============================
// SCHEDULER v1 — INVISIBLE CADENCE
// ===============================
function schedulerGate(posts) {
  const now = new Date();

  // Max 2 posts per calendar day
  const today = now.toISOString().split("T")[0];

  const todayPosts = posts.filter(p =>
    p.date && p.date.startsWith(today)
  );

  if (todayPosts.length >= 2) {
    throw new Error("⛔ SCHEDULER: Daily post limit reached");
  }

  // Randomized allowed publish window (local time)
  const hour = now.getHours();
  const allowedWindows = [
    [7, 11],   // morning
    [13, 16],  // afternoon
    [18, 21]   // evening
  ];

  const allowedNow = allowedWindows.some(
    ([start, end]) => hour >= start && hour <= end
  );

  if (!allowedNow) {
    throw new Error("⛔ SCHEDULER: Outside publish window");
  }

  console.log("✅ Scheduler gate passed");
}
async function runPipeline() {
  console.log("🚀 Running WaveSignals pipeline...");

  const researcher = runResearcher();
  const strategist = runStrategist(researcher);
  const content = await runWriter(researcher, strategist);

  const title = researcher.topic;

  // 🔐 PASS 2 — QUALITY CHECK
  qualityGate(title, content);

  const raw = fs.readFileSync(POSTS_PATH, "utf-8");
  const data = JSON.parse(raw);

  // Scheduler: ensure cadence and window
  schedulerGate(data.posts || []);

  writerGuard(content);

  // Strategist enforcement (format / depth / monetization rules)
  strategistGuard(strategist, content);

  publishPost(title, content);

  console.log("📌 Now run: node scripts/generate-sitemap.js");
}

runPipeline();
