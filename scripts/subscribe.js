document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('#subscribe-form, #email-form');
    const API_URL = 'https://mahendercreates-wavesignals-backend.hf.space/api';

    // Google Apps Script Web App URL for sheet integration
    const GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzLnN7sE4kXKp_VLgnxQvpWbJE3rY1gILWN8gUoCObT3l0LGwdS6ZrVYjWxBG8gfFAP/exec";

    forms.forEach(form => {
        if (!form) return;

        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const emailInput = form.querySelector('input[name="email"]');
            const submitBtn = form.querySelector('button[type="submit"]');
            const statusMsg = form.parentElement.querySelector('.status-message');

            if (!emailInput || !submitBtn) return;

            const email = emailInput.value.trim();

            // Disable form
            submitBtn.disabled = true;
            submitBtn.textContent = 'Joining...';
            if (statusMsg) statusMsg.textContent = '';

            try {
                // Send to backend API
                const backendResponse = await fetch(`${API_URL}/subscribers`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email })
                });

                const backendData = await backendResponse.json();

                // Send to Google Sheets (fire and forget - don't wait for response)
                if (GOOGLE_SCRIPT_URL) {
                    fetch(GOOGLE_SCRIPT_URL, {
                        method: 'POST',
                        mode: 'no-cors',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ email, timestamp: new Date().toISOString() })
                    }).catch(() => {
                        // Silently fail - Google Sheets is backup
                        console.log('Google Sheets backup failed (non-critical)');
                    });
                }

                // Show success message
                if (statusMsg) {
                    statusMsg.textContent = '✅ Thanks for subscribing!';
                    statusMsg.style.color = '#1A8917';
                }

                // Reset form
                emailInput.value = '';
                setTimeout(() => {
                    if (statusMsg) statusMsg.textContent = '';
                }, 5000);

            } catch (error) {
                console.error('Subscription error:', error);

                if (statusMsg) {
                    statusMsg.textContent = '❌ Subscription failed. Please try again.';
                    statusMsg.style.color = '#DC2626';
                }
            } finally {
                // Re-enable form
                submitBtn.disabled = false;
                submitBtn.textContent = 'Join';
            }
        });
    });
});
