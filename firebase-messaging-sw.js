// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Initialize Firebase
firebase.initializeApp({
    apiKey: "AIzaSyCZSGryxMCV1z_IxyWl_HfEtKZWR8PsqnA",
    authDomain: "wavesignals7.firebaseapp.com",
    projectId: "wavesignals7",
    storageBucket: "wavesignals7.firebasestorage.app",
    messagingSenderId: "344790294906",
    appId: "1:344790294906:web:88e75c8851b78cdada36c3",
    measurementId: "G-V63NG501C1"
});

const messaging = firebase.messaging();

// Handle background messages (when browser is closed or in background)
messaging.onBackgroundMessage((payload) => {
    console.log('Received background message:', payload);

    const notificationTitle = payload.notification.title || 'New Post on WaveSignals';
    const notificationOptions = {
        body: payload.notification.body || 'Check out our latest post!',
        icon: '/favicon.svg',
        badge: '/favicon.svg',
        tag: 'wavesignals-post',
        requireInteraction: false,
        data: { url: payload.data?.url || 'https://wavesignals.waveseed.app' }
    };

    return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    event.notification.close();

    const urlToOpen = event.notification.data.url || 'https://wavesignals.waveseed.app';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((windowClients) => {
                // Check if there's already a window open
                for (let client of windowClients) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Otherwise open new window
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});
