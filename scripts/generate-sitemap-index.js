const fs = require("fs");
const path = require("path");

// ALWAYS use custom domain - never Netlify subdomain
const SITE_URL = "https://wavesignals.waveseed.app";

function generateSitemapIndex() {
    const today = new Date().toISOString().split('T')[0];

    const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>${SITE_URL}/sitemap-pages.xml</loc>
    <lastmod>${today}</lastmod>
  </sitemap>
  <sitemap>
    <loc>${SITE_URL}/sitemap-posts.xml</loc>
    <lastmod>${today}</lastmod>
  </sitemap>
</sitemapindex>`;

    const outputPath = path.join(__dirname, "../sitemap.xml");
    fs.writeFileSync(outputPath, sitemap.trim());
    console.log("✅ sitemap.xml (index) generated with custom domain only");
}

generateSitemapIndex();
