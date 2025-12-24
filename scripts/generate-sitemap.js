const fs = require("fs");
const path = require("path");

// Use SITE_URL env var in CI or default to the production domain
const SITE_URL = process.env.SITE_URL || "https://wavesignals.waveseed.app";
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
  const homeLoc = SITE_URL ? `${SITE_URL.replace(/\/$/, '')}/app/index.html` : `/app/index.html`;
  urls.push(`
  <url>
    <loc>${homeLoc}</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  `);

  // Published posts
  posts
    .filter(p => p.published)
    .forEach(post => {
      const loc = SITE_URL ? `${SITE_URL.replace(/\/$/, '')}/app/post.html?slug=${post.slug}` : `/app/post.html?slug=${post.slug}`;
      urls.push(`
  <url>
    <loc>${loc}</loc>
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
