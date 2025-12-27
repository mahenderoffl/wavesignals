// Universal Ad Management System
// Supports: Google AdSense, Media.net, Carbon Ads, Direct Ads, Custom HTML

class UniversalAdManager {
    constructor() {
        this.config = null;
        this.networksLoaded = {};
    }

    async init() {
        try {
            const res = await fetch('/data/ads.json');
            this.config = await res.json();

            if (this.config.enabled) {
                this.loadEnabledNetworks();
            }
        } catch (e) {
            console.error('Ad config load error:', e);
        }
    }

    loadEnabledNetworks() {
        const networks = this.config.networks;

        // Load Google AdSense
        if (networks.adsense?.enabled && networks.adsense.publisherId) {
            this.loadAdSense(networks.adsense.publisherId);
        }

        // Load Media.net
        if (networks.medianet?.enabled && networks.medianet.publisherId) {
            this.loadMediaNet(networks.medianet.publisherId);
        }

        // Carbon Ads loads per-placement, no global script needed
    }

    loadAdSense(publisherId) {
        if (this.networksLoaded.adsense) return;

        const script = document.createElement('script');
        script.async = true;
        script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${publisherId}`;
        script.crossOrigin = 'anonymous';
        document.head.appendChild(script);

        this.networksLoaded.adsense = true;
    }

    loadMediaNet(publisherId) {
        if (this.networksLoaded.medianet) return;

        window._mNHandle = window._mNHandle || {};
        window._mNHandle.queue = window._mNHandle.queue || [];

        const script = document.createElement('script');
        script.async = true;
        script.src = `https://contextual.media.net/dmedianet.js?cid=${publisherId}`;
        document.head.appendChild(script);

        this.networksLoaded.medianet = true;
    }

    renderAd(placementKey, containerId) {
        if (!this.config || !this.config.enabled) return;

        const container = document.getElementById(containerId);
        if (!container) return;

        // Parse placement path
        const placement = this.getPlacement(placementKey);
        if (!placement || !placement.enabled) return;

        // Render based on network type
        switch (placement.network) {
            case 'adsense':
                this.renderAdSense(placement, container);
                break;
            case 'medianet':
                this.renderMediaNet(placement, container);
                break;
            case 'carbonads':
                this.renderCarbonAds(placement, container);
                break;
            case 'direct':
            case 'custom':
                this.renderCustomAd(placement, container);
                break;
            default:
                console.warn('Unknown ad network:', placement.network);
        }
    }

    getPlacement(placementKey) {
        const keys = placementKey.split('.');
        let placement = this.config.placements;
        for (const key of keys) {
            placement = placement[key];
            if (!placement) return null;
        }
        return placement;
    }

    renderAdSense(placement, container) {
        if (!placement.adSlot) return;

        const adWrapper = document.createElement('div');
        adWrapper.className = 'ad-container ad-adsense';
        adWrapper.style.cssText = this.getAdStyles(placement.size);

        const ins = document.createElement('ins');
        ins.className = 'adsbygoogle';
        ins.style.display = 'block';
        ins.setAttribute('data-ad-client', this.config.networks.adsense.publisherId);
        ins.setAttribute('data-ad-slot', placement.adSlot);

        const [width, height] = placement.size.split('x');
        ins.style.width = width + 'px';
        ins.style.height = height + 'px';

        adWrapper.appendChild(ins);
        container.appendChild(adWrapper);

        try {
            (adsbygoogle = window.adsbygoogle || []).push({});
        } catch (e) {
            console.error('AdSense error:', e);
        }
    }

    renderMediaNet(placement, container) {
        if (!placement.adSlot) return;

        const adWrapper = document.createElement('div');
        adWrapper.className = 'ad-container ad-medianet';
        adWrapper.style.cssText = this.getAdStyles(placement.size);

        const adDiv = document.createElement('div');
        adDiv.id = 'medianet-' + Math.random().toString(36).substr(2, 9);

        const [width, height] = placement.size.split('x');
        adDiv.setAttribute('data-cid', this.config.networks.medianet.publisherId);
        adDiv.setAttribute('data-crid', placement.adSlot);

        adWrapper.appendChild(adDiv);
        container.appendChild(adWrapper);

        try {
            window._mNHandle.queue.push(() => {
                window._mNDetails.loadTag(adDiv.id, width, height);
            });
        } catch (e) {
            console.error('Media.net error:', e);
        }
    }

    renderCarbonAds(placement, container) {
        const adWrapper = document.createElement('div');
        adWrapper.className = 'ad-container ad-carbon';
        adWrapper.style.cssText = this.getAdStyles(placement.size);

        const script = document.createElement('script');
        script.async = true;
        script.type = 'text/javascript';
        script.src = `//cdn.carbonads.com/carbon.js?serve=${placement.adSlot}&placement=${this.config.networks.carbonads.siteId}`;
        script.id = '_carbonads_js';

        adWrapper.appendChild(script);
        container.appendChild(adWrapper);
    }

    renderCustomAd(placement, container) {
        if (!placement.customCode) return;

        const adWrapper = document.createElement('div');
        adWrapper.className = 'ad-container ad-custom';
        adWrapper.style.cssText = this.getAdStyles(placement.size);
        adWrapper.innerHTML = placement.customCode;

        container.appendChild(adWrapper);
    }

    getAdStyles(size) {
        return `
      margin: 32px auto;
      text-align: center;
      background: #F9F9F9;
      border: 1px solid #E6E6E6;
      border-radius: 4px;
      padding: 16px;
      max-width: ${size.split('x')[0]}px;
    `;
    }

    // Render in-feed ads
    renderInFeed(placementKey, postsContainer, frequency) {
        if (!this.config || !this.config.enabled) return;

        const placement = this.getPlacement(placementKey);
        if (!placement || !placement.enabled) return;

        const posts = postsContainer.querySelectorAll('.article-item');
        posts.forEach((post, index) => {
            if ((index + 1) % (frequency || placement.frequency || 3) === 0) {
                const adContainer = document.createElement('div');
                adContainer.id = `ad-feed-${index}`;
                adContainer.className = 'ad-infeed-container';
                post.after(adContainer);
                this.renderAd(placementKey, `ad-feed-${index}`);
            }
        });
    }

    // Utility: Disable all ads
    disable() {
        document.querySelectorAll('.ad-container').forEach(ad => {
            ad.style.display = 'none';
        });
    }

    // Utility: Enable all ads
    enable() {
        document.querySelectorAll('.ad-container').forEach(ad => {
            ad.style.display = 'block';
        });
    }
}

// Global instance
window.adManager = new UniversalAdManager();
