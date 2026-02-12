/**
 * Push Notification Handler for WaveSignals
 * Handles Firebase Cloud Messaging subscription
 */

(function() {
    'use strict';

    // Firebase configuration
    const firebaseConfig = {
        apiKey: "AIzaSyC2SGry4MCvIz_IyyML-HFEtKZW8BPsqn4",
        authDomain: "wavesignals7.firebaseapp.com",
        projectId: "wavesignals7",
        storageBucket: "wavesignals7.firebasestorage.app",
        messagingSenderId: "344790294906",
        appId: "1:344790294906:web:88a75c885107Bcdada36c3",
        measurementId: "G-VD3NS50tc9"
    };

    const VAPID_KEY = "BDNrm1kZ8Zg3h4f3kGMHx_4eYa7z9N2qZ4X6F8f5n8wF7tZ8H4X3Y9F2d6w5P9V8J7L5K3G9H6f4";
    const API_URL = 'https://wave-signals.vercel.app/api';

    let firebaseApp = null;
    let messaging = null;

    // Initialize Firebase
    async function initializeFirebase() {
        if (firebaseApp) return;

        try {
            // Dynamically import Firebase
            const { initializeApp } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js');
            const { getMessaging, getToken, onMessage } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging.js');

            firebaseApp = initializeApp(firebaseConfig);
            messaging = getMessaging(firebaseApp);

            // Listen for foreground messages
            onMessage(messaging, (payload) => {
                console.log('Foreground notification received:', payload);
                showNotificationBanner(payload);
            });

            console.log('✅ Firebase initialized');
        } catch (error) {
            console.error('❌ Firebase initialization failed:', error);
        }
    }

    // Show in-page notification banner for foreground messages
    function showNotificationBanner(payload) {
        const title = payload.notification?.title || 'New Post';
        const body = payload.notification?.body || '';
        const url = payload.data?.url || '/';

        const banner = document.createElement('div');
        banner.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 16px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            max-width: 350px;
            z-index: 10000;
            cursor: pointer;
            animation: slideIn 0.3s ease-out;
        `;
        banner.innerHTML = `
            <div style="font-weight: 600; margin-bottom: 4px;">${title}</div>
            <div style="font-size: 14px; color: #666;">${body}</div>
        `;

        banner.onclick = () => {
            window.location.href = url;
        };

        document.body.appendChild(banner);

        setTimeout(() => {
            banner.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => banner.remove(), 300);
        }, 5000);
    }

    // Subscribe to push notifications
    async function subscribeToPushNotifications() {
        try {
            await initializeFirebase();

            if (!('Notification' in window)) {
                alert('❌ Your browser doesn\'t support notifications');
                return false;
            }

            console.log('Requesting notification permission...');
            const permission = await Notification.requestPermission();

            if (permission === 'granted') {
                console.log('✅ Permission granted');

                // Register service worker
                const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
                console.log('✅ Service worker registered');

                // Get FCM token
                const { getMessaging, getToken } = await import('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging.js');
                const msg = messaging || getMessaging(firebaseApp);
                
                const fcmToken = await getToken(msg, {
                    vapidKey: VAPID_KEY,
                    serviceWorkerRegistration: registration
                });

                if (fcmToken) {
                    console.log('✅ FCM Token:', fcmToken.substring(0, 20) + '...');

                    // Send token to backend
                    const response = await fetch(`${API_URL}/fcm-subscribe`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            token: fcmToken,
                            userAgent: navigator.userAgent
                        })
                    });

                    if (response.ok) {
                        console.log('✅ Subscribed to push notifications');
                        localStorage.setItem('ws_notifications_subscribed', 'true');
                        return true;
                    } else {
                        console.error('❌ Backend subscription failed');
                        return false;
                    }
                } else {
                    console.error('❌ No FCM token received');
                    return false;
                }
            } else {
                console.log('❌ Permission denied');
                return false;
            }
        } catch (error) {
            console.error('❌ Subscription error:', error);
            return false;
        }
    }

    // Check if already subscribed
    function isSubscribed() {
        return localStorage.getItem('ws_notifications_subscribed') === 'true';
    }

    // Show notification prompt
    function showNotificationPrompt() {
        if (isSubscribed()) return;
        if (!('Notification' in window)) return;
        if (Notification.permission === 'denied') return;

        // Show prompt after 5 seconds
        setTimeout(() => {
            const prompt = document.createElement('div');
            prompt.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 16px 20px;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
                max-width: 350px;
                z-index: 10000;
                animation: slideUp 0.4s ease-out;
            `;
            prompt.innerHTML = `
                <div style="display: flex; align-items: start; gap: 12px;">
                    <div style="font-size: 24px;">🔔</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 600; margin-bottom: 4px;">Stay Updated!</div>
                        <div style="font-size: 14px; margin-bottom: 12px; opacity: 0.9;">
                            Get notified when we publish new insights
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button id="ws-enable-notifications" style="
                                background: white;
                                color: #667eea;
                                border: none;
                                padding: 8px 16px;
                                border-radius: 6px;
                                font-weight: 600;
                                cursor: pointer;
                                font-size: 14px;
                            ">Enable</button>
                            <button id="ws-dismiss-notifications" style="
                                background: rgba(255,255,255,0.2);
                                color: white;
                                border: none;
                                padding: 8px 16px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 14px;
                            ">Later</button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(prompt);

            // Add CSS animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideUp {
                    from { transform: translateY(100px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                @keyframes slideIn {
                    from { transform: translateX(400px); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(400px); opacity: 0; }
                }
            `;
            document.head.appendChild(style);

            document.getElementById('ws-enable-notifications').onclick = async () => {
                const success = await subscribeToPushNotifications();
                if (success) {
                    prompt.innerHTML = '<div style="text-align: center; padding: 8px;">✅ Notifications enabled!</div>';
                    setTimeout(() => prompt.remove(), 2000);
                }
            };

            document.getElementById('ws-dismiss-notifications').onclick = () => {
                localStorage.setItem('ws_notification_prompt_dismissed', Date.now());
                prompt.remove();
            };

            // Auto dismiss after 15 seconds
            setTimeout(() => prompt.remove(), 15000);
        }, 5000);
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', showNotificationPrompt);
    } else {
        showNotificationPrompt();
    }

    // Expose global function for manual subscription
    window.enableNotifications = subscribeToPushNotifications;

})();
