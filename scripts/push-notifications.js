/**
 * Push Notification Handler for WaveSignals
 * Handles Firebase Cloud Messaging subscription
 */

(function() {
    'use strict';

    // Firebase configuration
    const firebaseConfig = {
        apiKey: "AIzaSyCZSGryxMCV1z_IxyWl_HfEtKZWR8PsqnA",
        authDomain: "wavesignals7.firebaseapp.com",
        projectId: "wavesignals7",
        storageBucket: "wavesignals7.firebasestorage.app",
        messagingSenderId: "344790294906",
        appId: "1:344790294906:web:88e75c8851b78cdada36c3",
        measurementId: "G-V63NG501C1"
    };

    const VAPID_KEY = "BPqPXddSZtqw4tf4-yoqud8sSqL66R7hk8wbsO9P1jsF-AOFnGRWT74aC2EO8R4mno12bPSJBORJ7nuqiF1hkrE";
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
    async function subscribeToPushNotifications(buttonElement) {
        try {
            // Show loading state
            if (buttonElement) {
                buttonElement.disabled = true;
                buttonElement.innerHTML = '⏳ Enabling...';
            }

            // Check if already subscribed
            if (isSubscribed() && Notification.permission === 'granted') {
                if (buttonElement) {
                    buttonElement.innerHTML = '✅ Already Enabled';
                    setTimeout(() => {
                        if (buttonElement.parentElement) {
                            buttonElement.parentElement.parentElement.remove();
                        }
                    }, 2000);
                }
                return { success: true, message: 'Already subscribed' };
            }

            await initializeFirebase();

            if (!('Notification' in window)) {
                if (buttonElement) {
                    buttonElement.disabled = false;
                    buttonElement.innerHTML = 'Enable';
                }
                return { success: false, message: 'Your browser doesn\'t support notifications' };
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

                    const data = await response.json().catch(() => ({}));

                    if (response.ok && data.success) {
                        console.log('✅ Subscribed to push notifications');
                        localStorage.setItem('ws_notifications_subscribed', 'true');
                        if (buttonElement) {
                            buttonElement.innerHTML = '✅ Enabled!';
                        }
                        return { success: true, message: 'Notifications enabled successfully!' };
                    } else {
                        console.error('❌ Backend subscription failed:', data);
                        if (buttonElement) {
                            buttonElement.disabled = false;
                            buttonElement.innerHTML = 'Enable';
                        }
                        return { success: false, message: data.error || 'Failed to subscribe on server' };
                    }
                } else {
                    console.error('❌ No FCM token received');
                    if (buttonElement) {
                        buttonElement.disabled = false;
                        buttonElement.innerHTML = 'Enable';
                    }
                    return { success: false, message: 'Failed to get notification token' };
                }
            } else if (permission === 'denied') {
                console.log('❌ Permission denied');
                if (buttonElement) {
                    buttonElement.disabled = false;
                    buttonElement.innerHTML = 'Enable';
                }
                return { success: false, message: 'You blocked notifications. Please enable them in browser settings.' };
            } else {
                console.log('❌ Permission not granted');
                if (buttonElement) {
                    buttonElement.disabled = false;
                    buttonElement.innerHTML = 'Enable';
                }
                return { success: false, message: 'Permission not granted' };
            }
        } catch (error) {
            console.error('❌ Subscription error:', error);
            if (buttonElement) {
                buttonElement.disabled = false;
                buttonElement.innerHTML = 'Enable';
            }
            return { success: false, message: error.message || 'An error occurred' };
        }
    }

    // Check if already subscribed
    function isSubscribed() {
        return localStorage.getItem('ws_notifications_subscribed') === 'true';
    }

    // Show notification prompt
    function showNotificationPrompt() {
        // Don't show if already subscribed
        if (isSubscribed() && Notification.permission === 'granted') {
            console.log('✅ Already subscribed to notifications');
            return;
        }
        
        // Don't show if browser doesn't support notifications
        if (!('Notification' in window)) {
            console.log('❌ Browser doesn\'t support notifications');
            return;
        }
        
        // Don't show if permission was denied
        if (Notification.permission === 'denied') {
            console.log('❌ Notification permission denied');
            return;
        }

        // Don't show if dismissed recently (within 24 hours)
        const dismissedTime = localStorage.getItem('ws_notification_prompt_dismissed');
        if (dismissedTime && (Date.now() - parseInt(dismissedTime)) < 24 * 60 * 60 * 1000) {
            console.log('⏸️ Notification prompt dismissed recently');
            return;
        }

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

            document.getElementById('ws-enable-notifications').onclick = async (e) => {
                const button = e.target;
                const result = await subscribeToPushNotifications(button);
                
                if (result.success) {
                    // Show success message
                    prompt.innerHTML = `
                        <div style="text-align: center; padding: 16px;">
                            <div style="font-size: 32px; margin-bottom: 8px;">✅</div>
                            <div style="font-weight: 600; margin-bottom: 4px;">All Set!</div>
                            <div style="font-size: 14px; opacity: 0.9;">${result.message}</div>
                        </div>
                    `;
                    setTimeout(() => prompt.remove(), 2500);
                } else {
                    // Show error message
                    prompt.innerHTML = `
                        <div style="padding: 16px;">
                            <div style="display: flex; align-items: start; gap: 12px;">
                                <div style="font-size: 24px;">❌</div>
                                <div style="flex: 1;">
                                    <div style="font-weight: 600; margin-bottom: 4px;">Oops!</div>
                                    <div style="font-size: 14px; margin-bottom: 12px; opacity: 0.9;">
                                        ${result.message}
                                    </div>
                                    <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()" style="
                                 async () => {
        const result = await subscribeToPushNotifications(null);
        if (result.success) {
            alert('✅ ' + result.message);
        } else {
            alert('❌ ' + result.message);
        }
        return result.success;
    }
                                        color: #667eea;
                                        border: none;
                                        padding: 8px 16px;
                                        border-radius: 6px;
                                        font-weight: 600;
                                        cursor: pointer;
                                        font-size: 14px;
                                    ">Close</button>
                                </div>
                            </div>
                        </div>
                    `;
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
