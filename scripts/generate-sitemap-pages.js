const fs = require("fs");
const path = require("path");

// ALWAYS use custom domain - never Netlify subdomain
const SITE_URL = "https://wavesignals.waveseed.app";

function generatePagesSitemap() {
    const pages = [
        { url: `${SITE_URL}/app/index.html`, priority: "1.0", changefreq: "daily" },
        { url: `${SITE_URL}/app/blog.html`, priority: "0.9", changefreq: "daily" },
        { url: `${SITE_URL}/about.html`, priority: "0.7", changefreq: "monthly" },
        { url: `${SITE_URL}/contact.html`, priority: "0.6", changefreq: "monthly" },
        { url: `${SITE_URL}/privacy.html`, priority: "0.5", changefreq: "yearly" },
        { url: `${SITE_URL}/terms.html`, priority: "0.5", changefreq: "yearly" }
    ];

    const urls = pages.map(page => `
  <url>
    <loc>${page.url}</loc>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`).join("");

    const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>`;

    const outputPath = path.join(__dirname, "../sitemap-pages.xml");
    fs.writeFileSync(outputPath, sitemap.trim());
    console.log("✅ sitemap-pages.xml generated with custom domain");
}

generatePagesSitemap();
