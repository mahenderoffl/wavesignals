const fs = require("fs");
const path = require("path");

// ALWAYS use custom domain - NEVER use Netlify subdomain for SEO
const SITE_URL = "https://wavesignals.waveseed.app";
const POSTS_PATH = path.join(__dirname, "../data/posts.json");
const OUTPUT_PATH = path.join(__dirname, "../sitemap-posts.xml");

function formatDate(date) {
  return new Date(date).toISOString();
}

function generatePostsSitemap() {
  const raw = fs.readFileSync(POSTS_PATH, "utf-8");
  const data = JSON.parse(raw);

  const posts = Array.isArray(data.posts) ? data.posts : [];

  const urls = [];

  // Published posts only
  posts
    .filter(p => p.published)
    .forEach(post => {
      const loc = `${SITE_URL}/app/post.html?slug=${post.slug}`;
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
  console.log(`✅ sitemap-posts.xml generated successfully with ${urls.length} posts (custom domain only)`);
}

generatePostsSitemap();
