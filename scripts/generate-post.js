/**
 * AUTOMATED CONTENT GENERATOR (Multi-Agent)
 * 
 * Usage: node scripts/generate-post.js "Topic Name"
 * 
 * Architecture:
 * 1. Researcher Agent: Search web (mock/real) for facts.
 * 2. Writer Agent: Draft content based on research.
 * 3. Editor Agent: Critique & Humanize.
 * 4. Publisher Agent: Commit to data/posts.json.
 */

const fs = require('fs').promises;
const path = require('path');

// --- CONFIG ---
const POSTS_FILE = path.join(__dirname, '../data/posts.json');
const MOCK_DELAY = 1000;

// --- GEMINI CONFIG ---
// npm install @google/generative-ai
const { GoogleGenerativeAI } = require("@google/generative-ai");

async function callLLM(prompt, systemRole) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.warn("[WARN] No GEMINI_API_KEY found. Falling back to Mock.");
    return `[MOCK CONTENT by ${systemRole}] - ${prompt.substring(0, 50)}...`;
  }

  try {
    const genAI = new GoogleGenerativeAI(apiKey);
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

    // Combine system role and prompt for Gemini
    const fullPrompt = `
      ROLE: You are an expert ${systemRole} for a tech blog called WaveSignals.
      TASK: ${prompt}
      Tone: Professional, Insightful, yet human.
      Output: Return only the requested content, no conversational filler.
    `;

    const result = await model.generateContent(fullPrompt);
    const response = await result.response;
    return response.text();
  } catch (error) {
    console.error(`[AI ERROR] ${systemRole} failed:`, error);
    return `[Error generating content: ${error.message}]`;
  }
}

// --- AGENTS ---

async function generateTopic() {
  const topics = [
    "AI Coding Agents", "DevOps Automation", "Future of React", "WebAssembly",
    "Rust vs Go", "Serverless Architecture", "Edge Computing", "Cybersecurity in 2025",
    "Quantum Computing", "No-Code Revolution", "Tech Layoffs & Hiring", "Green Tech"
  ];
  const seed = topics[Math.floor(Math.random() * topics.length)];

  return await callLLM(`
    Suggest a unique, catchy, specific blog post title about "${seed}" or a related tech trend for 2025.
    Return ONLY the raw title text. No quotes.
  `, 'Editor-in-Chief');
}

async function researchTopic(topic) {
  return await callLLM(`
    Research the topic: "${topic}".
    Provide 5 unique, data-backed facts or trends relevant to 2024/2025.
    Focus on developer tools, AI coding, or software architecture.
    Source freely from your knowledge base.
  `, 'Researcher');
}

async function writeDraft(topic, research) {
  return await callLLM(`
    Write a comprehensive blog post draft about "${topic}".
    Use these research notes:
     ${research}
    
    Structure:
    - Catchy H2 Title
    - Engaging Introduction (Hook)
    - 3-4 Detailed H3 Sections
    - Conclusion
    - Format in clean HTML (<p>, <h2>, <h3>, <ul>).
  `, 'Writer');
}

async function humanizeContent(draft) {
  return await callLLM(`
    Act as a Senior Editor. Improve this draft:
     ${draft}
    
    Guidelines:
    1. Fix any robotic phrasing. Make it sound like a passionate engineer wrote it.
    2. Ensure HTML formatting is perfect.
    3. Add a "Key Takeaways" section at the end if missing.
    4. Return ONLY the final HTML content.
  `, 'Editor');
}

// --- MAIN WORKFLOW ---

async function main() {
  let topic = process.argv[2];

  if (!topic) {
    console.log("[BOT] No topic provided. Generating one...");
    topic = await generateTopic();
  }

  console.log(`[BOT] Starting job for: "${topic}"`);

  // 1. Research
  const research = await researchTopic(topic);
  console.log(`[BOT] Research Complete.`);

  // 2. Draft
  const draft = await writeDraft(topic, research);
  console.log(`[BOT] Draft Complete.`);

  // 3. Humanize
  const finalContent = await humanizeContent(draft);
  console.log(`[BOT] Humanization Complete.`);

  // 4. Publish
  try {
    const fileData = await fs.readFile(POSTS_FILE, 'utf8');
    const db = JSON.parse(fileData);

    const newPost = {
      id: "bot-" + Date.now(),
      title: topic,
      slug: topic.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      excerpt: "Automated analysis on " + topic,
      content: finalContent,
      date: new Date().toISOString(),
      published: true,
      status: "published",
      author: "WaveSignals Team"
    };

    db.posts.unshift(newPost);
    await fs.writeFile(POSTS_FILE, JSON.stringify(db, null, 2));
    console.log(`[BOT] Published successfully to data/posts.json`);
  } catch (e) {
    console.error(`[BOT] Failed to publish:`, e);
  }
}

main();
