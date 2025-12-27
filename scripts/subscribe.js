// WaveSignals Newsletter Subscription
// Works both locally (backend API) and on Netlify (Netlify Forms)

async function handleSubscribe(event) {
    event.preventDefault();
    const form = event.target;
    const emailInput = form.querySelector('input[type="email"]');
    const email = emailInput.value;
    const status = form.querySelector('.status-message');
    const btn = form.querySelector('button[type="submit"]');

    if (!status) return; // Skip if no status element

    const originalText = btn.innerText;
    btn.innerText = "Sending...";
    btn.disabled = true;
    status.textContent = '';
    status.style.display = 'block';

    // Local development: use backend API
    const API_URL = "https://mahendercreates-wavesignals-backend.hf.space/api/subscribers";
    const GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbztdybtQQOH5ZOsCEM6XtpL9uQsK7f1aiSV4eU-HnibQBGGtitOwhkk1XW-lNdnT5-Y/exec"; // Updated to correct Google Sheets URL

    try {
        // 1. Send to Backend Database
        const dbPromise = fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        // 2. Send to Google Sheets (Fire and forget, no-cors)
        const sheetPromise = fetch(GOOGLE_SCRIPT_URL, {
            method: "POST",
            headers: { "Content-Type": "text/plain;charset=utf-8" }, // Google Apps Script likes text/plain
            body: JSON.stringify({ email }),
            mode: "no-cors" // Essential for calling GAS from browser
        });

        // Wait for DB response (primary source of truth)
        const res = await dbPromise;

        // Note: We don't await sheetPromise specifically to block success, 
        // effectively treating it as a background "side effect"

        if (res.ok) {
            form.reset();
            status.innerHTML = "✓ Successfully subscribed! Check your email.";
            status.style.color = "#1A8917"; // Green
            status.style.fontWeight = "600";
            btn.innerText = "Subscribed ✓";
            btn.style.background = "#1A8917";

            // Keep success state visible
            setTimeout(() => {
                status.innerHTML = "";
                status.style.display = "none";
            }, 5000);
        } else {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.message || "Server error");
        }
    } catch (e) {
        status.innerHTML = `✗ ${e.message || "Failed to subscribe. Please try again."}`;
        status.style.color = "#DC2626";
        status.style.fontWeight = "600";
    } finally {
        setTimeout(() => {
            btn.disabled = false;
            if (btn.innerText !== "Subscribed ✓") {
                btn.innerText = originalText;
                btn.style.background = "";
            }
        }, 3000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    ['subscribe-form', 'email-form'].forEach(id => {
        const form = document.getElementById(id);
        if (form) {
            // Always intercept form submission
            console.log(`Attaching submit listener to ${id}`);
            form.addEventListener('submit', handleSubscribe);
        }
    });
});
