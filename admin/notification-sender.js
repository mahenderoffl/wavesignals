/* Custom Notification Sender for Admin Panel */

// Global subscribers list
let fcmSubscribers = [];

// Load FCM subscribers for selection
async function loadFCMSubscribersForSelection() {
    try {
        const response = await fetch('https://wave-signals.vercel.app/api/fcm-subscribers', {
            headers: {
                'X-Admin-Key': sessionStorage.getItem('ws_admin')
            }
        });

        const data = await response.json();
        fcmSubscribers = data.subscribers || [];
        
        const listContainer = document.getElementById('subscriber-selection-list');
        
        if (fcmSubscribers.length === 0) {
            listContainer.innerHTML = '<div style="text-align: center; color: #666; font-size: 13px; padding: 12px;">No subscribers available</div>';
            return;
        }

        listContainer.innerHTML = fcmSubscribers.map((sub, index) => {
            const deviceInfo = sub.device_type || 'Unknown Device';
            const subscribedDate = new Date(sub.created_at).toLocaleDateString();
            return `
                <label style="display: flex; align-items: center; gap: 8px; padding: 8px; margin-bottom: 6px; cursor: pointer; border-radius: 4px; background: #f9fafb; color: #222;" onmouseover="this.style.background='#f3f4f6'" onmouseout="this.style.background='#f9fafb'">
                    <input type="checkbox" class="subscriber-checkbox" data-token="${sub.token}" data-index="${index}" onchange="updateSelectedCount()" 
                        style="width: 16px; height: 16px; cursor: pointer;">
                    <div style="flex: 1;">
                        <div style="font-size: 13px; font-weight: 500;">${deviceInfo}</div>
                        <div style="font-size: 11px; color: #666;">Subscribed: ${subscribedDate}</div>
                    </div>
                </label>
            `;
        }).join('');

        updateSelectedCount();
    } catch (error) {
        console.error('Error loading subscribers:', error);
        document.getElementById('subscriber-selection-list').innerHTML = 
            '<div style="text-align: center; color: #dc2626; font-size: 13px; padding: 12px;">Error loading subscribers</div>';
    }
}

// Toggle all subscribers selection
function toggleAllSubscribers(checkbox) {
    const checkboxes = document.querySelectorAll('.subscriber-checkbox');
    checkboxes.forEach(cb => cb.checked = checkbox.checked);
    updateSelectedCount();
}

// Update selected count display
function updateSelectedCount() {
    const selected = document.querySelectorAll('.subscriber-checkbox:checked').length;
    const total = fcmSubscribers.length;
    document.getElementById('selected-count').textContent = `(${selected} of ${total} selected)`;
    
    // Update select-all checkbox state
    const selectAll = document.getElementById('select-all-subscribers');
    if (selectAll) {
        selectAll.checked = selected === total && total > 0;
        selectAll.indeterminate = selected > 0 && selected < total;
    }
}

// Send custom notification to selected subscribers
async function sendCustomNotificationToSelected() {
    const title = document.getElementById('custom-notification-title').value.trim();
    const body = document.getElementById('custom-notification-body').value.trim();
    const url = document.getElementById('custom-notification-url').value.trim();

    if (!title || !body) {
        showNotificationStatus('❌ Please enter both title and message', 'error');
        return;
    }

    // Get selected tokens
    const selectedCheckboxes = document.querySelectorAll('.subscriber-checkbox:checked');
    if (selectedCheckboxes.length === 0) {
        showNotificationStatus('❌ Please select at least one subscriber', 'error');
        return;
    }

    const selectedTokens = Array.from(selectedCheckboxes).map(cb => cb.dataset.token);

    const sendBtn = document.getElementById('send-custom-notification-btn');
    const originalText = sendBtn.textContent;
    sendBtn.disabled = true;
    sendBtn.textContent = '📤 Sending...';
    showNotificationStatus('⏳ Sending notification...', 'info');

    try {
        const response = await fetch('https://wave-signals.vercel.app/api/send-notification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': sessionStorage.getItem('ws_admin')
            },
            body: JSON.stringify({ 
                title, 
                body, 
                url,
                tokens: selectedTokens
            })
        });

        const result = await response.json();

        if (result.success) {
            showNotificationStatus(`✅ Notification sent to ${result.sent} subscriber(s)!`, 'success');
            clearNotificationForm();
        } else {
            showNotificationStatus(`❌ Failed: ${result.error}`, 'error');
        }
    } catch (error) {
        showNotificationStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = originalText;
    }
}

// Show notification status message
function showNotificationStatus(message, type) {
    const statusDiv = document.getElementById('notification-status');
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#3b82f6'
    };
    statusDiv.style.color = colors[type] || '#666';
    statusDiv.textContent = message;
    
    if (type === 'success') {
        setTimeout(() => {
            statusDiv.textContent = '';
        }, 5000);
    }
}

// Clear notification form
function clearNotificationForm() {
    document.getElementById('custom-notification-title').value = '';
    document.getElementById('custom-notification-body').value = '';
    document.getElementById('custom-notification-url').value = '';
    document.querySelectorAll('.subscriber-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('select-all-subscribers').checked = false;
    updateSelectedCount();
    document.getElementById('notification-status').textContent = '';
}

// Send custom notification function (legacy - kept for backward compatibility)
async function sendCustomNotification() {
    const title = document.getElementById('notification-title').value.trim();
    const body = document.getElementById('notification-body').value.trim();
    const url = document.getElementById('notification-url').value.trim();

    if (!title || !body) {
        alert('Please enter both title and message');
        return;
    }

    const sendBtn = document.getElementById('send-notification-btn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';

    try {
        const response = await fetch('https://wave-signals.vercel.app/api/notifications/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Admin-Key': sessionStorage.getItem('ws_admin')
            },
            body: JSON.stringify({ title, body, url })
        });

        const result = await response.json();

        if (result.success) {
            alert(`✅ Notification sent to ${result.sent} subscribers!`);
            // Clear form
            document.getElementById('notification-title').value = '';
            document.getElementById('notification-body').value = '';
            document.getElementById('notification-url').value = '';
        } else {
            alert(`❌ Failed to send: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send Notification';
    }
}

// Load subscriber list
async function loadNotificationSubscribers() {
    try {
        const response = await fetch('https://wave-signals.vercel.app/api/notifications/subscribers', {
            headers: {
                'X-Admin-Key': sessionStorage.getItem('ws_admin')
            }
        });

        const data = await response.json();
        const tbody = document.getElementById('subscribers-tbody');

        if (data.subscribers && data.subscribers.length > 0) {
            tbody.innerHTML = data.subscribers.map((sub, index) => `
                <tr>
                    <td>${index + 1}</td>
                    <td>${sub.device_type || 'Unknown'}</td>
                    <td>${new Date(sub.created_at).toLocaleDateString()}</td>
                    <td>${sub.last_used ? new Date(sub.last_used).toLocaleDateString() : 'Never'}</td>
                    <td><span class="badge badge-published">Active</span></td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:32px;">No subscribers yet</td></tr>';
        }
    } catch (error) {
        console.error('Error loading subscribers:', error);
    }
}

//Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Load subscribers when notifications view is shown
    const notificationsTab = document.querySelector('[data-view="notifications"]');
    if (notificationsTab) {
        notificationsTab.addEventListener('click', () => {
            loadNotificationSubscribers();
            loadFCMSubscribersForSelection();
        });
    }
    
    // If already on notifications view, load immediately
    const notificationsView = document.getElementById('view-notifications');
    if (notificationsView && !notificationsView.classList.contains('hidden')) {
        loadFCMSubscribersForSelection();
    }
});


