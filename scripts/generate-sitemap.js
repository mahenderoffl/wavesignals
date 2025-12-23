const fs = require("fs");
const path = require("path");

const SITE_URL = "http://localhost:8080"; // change to real domain later
const POSTS_PATH = path.join(__dirname, "../data/posts.json");
const OUTPUT_PATH = path.join(__dirname, "../sitemap.xml");

function formatDate(date) {
  return new Date(date).toISOString();
}

function generateSitemap() {
  const raw = fs.readFileSync(POSTS_PATH, "utf-8");
  const data = JSON.parse(raw);

  const posts = Array.isArray(data.posts) ? data.posts : [];

  const urls = [];

  // Homepage
  urls.push(`
  <url>
    <loc>${SITE_URL}/app/index.html</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  `);

  // Published posts
  posts
    .filter(p => p.published)
    .forEach(post => {
      urls.push(`
  <url>
    <loc>${SITE_URL}/app/post.html?slug=${post.slug}</loc>
    <lastmod>${formatDate(post.date)}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
      `);
    });

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join("")}
</urlset>`;

  fs.writeFileSync(OUTPUT_PATH, sitemap.trim());
  console.log("✅ sitemap.xml generated successfully");
}

generateSitemap();
