/**
 * WaveSignals Quality Gate
 * Blocks weak / risky content before publish
 */

const fs = require("fs");
const path = require("path");

const POSTS_PATH = path.join(__dirname, "../data/posts.json");

// ---- CONFIG ----
const MIN_WORDS = 600;
const BANNED_PHRASES = [
  "in this article",
  "this article will",
  "we will explore",
  "let us explore",
  "as an ai",
  "lorem ipsum",
  "[paste",
  "placeholder"
];

// ---- HELPERS ----
function stripHtml(html) {
  return html.replace(/<[^>]*>/g, " ");
}

function wordCount(text) {
  return stripHtml(text)
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}

function hasHook(content) {
  const firstPara = content
    .split("</p>")[0]
    .replace(/<[^>]+>/g, "")
    .trim();

  return firstPara.length >= 80 && !firstPara.endsWith(":");
}

function containsBanned(content) {
  const lower = content.toLowerCase();
  return BANNED_PHRASES.some(p => lower.includes(p));
}

function isDuplicateTitle(title, posts) {
  return posts.some(
    p => p.title.toLowerCase() === title.toLowerCase()
  );
}

// ---- MAIN CHECK ----
function validatePost({ title, content }, existingPosts) {
  const errors = [];

  if (!title || title.length < 10) {
    errors.push("Title too short");
  }

  if (isDuplicateTitle(title, existingPosts)) {
    errors.push("Duplicate title");
  }

  const words = wordCount(content);
  if (words < MIN_WORDS) {
    errors.push(`Word count too low (${words})`);
  }

  if (!hasHook(content)) {
    errors.push("Weak or missing hook paragraph");
  }

  if (containsBanned(content)) {
    errors.push("Contains banned / placeholder phrases");
  }

  return {
    ok: errors.length === 0,
    errors
  };
}

// ---- EXPORT ----
module.exports = function runQualityGate(draftPost) {
  const raw = fs.readFileSync(POSTS_PATH, "utf-8");
  const data = JSON.parse(raw);

  const result = validatePost(draftPost, data.posts || []);

  if (!result.ok) {
    console.error("❌ QUALITY GATE FAILED");
    result.errors.forEach(e => console.error(" -", e));
    process.exit(1);
  }

  console.log("✅ QUALITY GATE PASSED");
  return true;
};
