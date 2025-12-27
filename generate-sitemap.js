// Dynamic sitemap generator for blog posts
// Run this to generate sitemap-posts.xml

const fs = require('fs');
const path = require('path');

const API_URL = 'https://mahendercreates-wavesignals-backend.hf.space/api';
const SITE_URL = 'https://wavesignals.waveseed.app';

async function generatePostsSitemap() {
    try {
        const response = await fetch(`${API_URL}/posts`);
        const data = await response.json();
        const posts = data.posts || [];

        const publishedPosts = posts.filter(p => p.published);

        const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${publishedPosts.map(post => `  <url>
    <loc>${SITE_URL}/app/post.html?slug=${post.slug}</loc>
    <lastmod>${new Date(post.date).toISOString().split('T')[0]}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>`).join('\n')}
</urlset>`;

        fs.writeFileSync('sitemap-posts.xml', sitemap);
        console.log(`✅ Generated sitemap for ${publishedPosts.length} posts`);
    } catch (error) {
        console.error('❌ Error generating sitemap:', error);
    }
}

generatePostsSitemap();
