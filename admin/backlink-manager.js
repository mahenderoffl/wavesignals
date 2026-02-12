/* Backlink Manager JavaScript - Add this to admin/panel.html */

// Wrap in IIFE to avoid global variable conflicts
(function () {
    'use strict';

    // Backlink Manager Implementation
    let backlinks = [];

    // Load backlinks from localStorage
    function loadBacklinks() {
        const stored = localStorage.getItem('backlinks');
        backlinks = stored ? JSON.parse(stored) : [];
        updateBacklinksUI();
    }

    // Save backlinks to localStorage
    function saveBacklinks() {
        localStorage.setItem('backlinks', JSON.stringify(backlinks));
        updateBacklinksUI();
    }

    // Update backlinks UI
    function updateBacklinksUI() {
        // Update stats
        const total = backlinks.length;
        const pending = backlinks.filter(b => b.status === 'pending').length;
        const active = backlinks.filter(b => b.status === 'active').length;
        const broken = backlinks.filter(b => b.status === 'broken').length;

        document.getElementById('total-backlinks').textContent = total;
        document.getElementById('pending-backlinks').textContent = pending;
        document.getElementById('active-backlinks').textContent = active;
        document.getElementById('broken-backlinks').textContent = broken;

        // Update progress bar
        const progress = Math.min((total / 50) * 100, 100);
        document.getElementById('backlink-progress').style.width = progress + '%';

        // Count this month's backlinks
        const thisMonth = backlinks.filter(b => {
            const added = new Date(b.addedDate);
            const now = new Date();
            return added.getMonth() === now.getMonth() && added.getFullYear() === now.getFullYear();
        }).length;
        document.getElementById('monthly-backlinks').textContent = thisMonth + ' added';

        // Update table
        const tbody = document.getElementById('backlinks-tbody');
        if (backlinks.length === 0) {
            tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 48px; color: var(--gray-400);">
                    No backlinks tracked yet. Click "+ Add Backlink" to start building your SEO profile.
                </td>
            </tr>
        `;
        } else {
            tbody.innerHTML = backlinks.map(backlink => `
            <tr>
                <td>
                    <div style="font-weight: 500;">${backlink.sourceWebsite}</div>
                    <div style="font-size: 13px; color: var(--gray-600);">
                        <a href="${backlink.url}" target="_blank" style="color: var(--gray-600);">${backlink.url}</a>
                    </div>
                </td>
                <td>${backlink.linkType}</td>
                <td>
                    <span class="badge badge-${backlink.status === 'active' ? 'published' : 'draft'}">
                        ${backlink.status}
                    </span>
                </td>
                <td>${new Date(backlink.addedDate).toLocaleDateString()}</td>
                <td>
                    <button onclick="editBacklink(${backlink.id})" style="background: none; border: none; cursor: pointer; padding: 4px 8px;">✏️</button>
                    <button onclick="deleteBacklink(${backlink.id})" style="background: none; border: none; cursor: pointer; padding: 4px 8px;">🗑️</button>
                </td>
            </tr>
        `).join('');
        }
    }

    // Show add backlink modal
    function showAddBacklinkModal() {
        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h2 class="modal-title">Add New Backlink</h2>
                <button onclick="closeBacklinkModal()" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">Source Website</label>
                    <input type="text" id="backlink-source" class="form-input" placeholder="example.com" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Backlink URL</label>
                    <input type="url" id="backlink-url" class="form-input" placeholder="https://example.com/link-to-wavesignals" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Link Type</label>
                    <select id="backlink-type" class="form-input">
                        <option value="Guest Post">Guest Post</option>
                        <option value="Directory">Directory</option>
                        <option value="Resource Page">Resource Page</option>
                        <option value="Forum">Forum</option>
                        <option value="Comment">Comment</option>
                        <option value="Social Media">Social Media</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Status</label>
                    <select id="backlink-status" class="form-input">
                        <option value="pending">Pending</option>
                        <option value="active">Active</option>
                        <option value="broken">Broken</option>
                    </select>
                </div>
            </div>
            <div class="form-actions">
                <button class="btn btn-secondary" onclick="closeBacklinkModal()">Cancel</button>
                <button class="btn btn-primary" onclick="saveNewBacklink()">Add Backlink</button>
            </div>
        </div>
    `;
        document.body.appendChild(modal);
        modal.id = 'backlink-modal';
    }

    // Close backlink modal
    function closeBacklinkModal() {
        const modal = document.getElementById('backlink-modal');
        if (modal) {
            modal.remove();
        }
    }

    // Save new backlink
    function saveNewBacklink() {
        const source = document.getElementById('backlink-source').value.trim();
        const url = document.getElementById('backlink-url').value.trim();
        const type = document.getElementById('backlink-type').value;
        const status = document.getElementById('backlink-status').value;

        if (!source || !url) {
            alert('Please fill in all required fields');
            return;
        }

        const newBacklink = {
            id: Date.now(),
            sourceWebsite: source,
            url: url,
            linkType: type,
            status: status,
            addedDate: new Date().toISOString()
        };

        backlinks.push(newBacklink);
        saveBacklinks();
        closeBacklinkModal();

        alert('✅ Backlink added successfully!');
    }

    // Edit backlink
    function editBacklink(id) {
        const backlink = backlinks.find(b => b.id === id);
        if (!backlink) return;

        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.innerHTML = `
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h2 class="modal-title">Edit Backlink</h2>
                <button onclick="closeEditBacklinkModal()" style="background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label class="form-label">Source Website</label>
                    <input type="text" id="edit-backlink-source" class="form-input" value="${backlink.sourceWebsite}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Backlink URL</label>
                    <input type="url" id="edit-backlink-url" class="form-input" value="${backlink.url}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Link Type</label>
                    <select id="edit-backlink-type" class="form-input">
                        <option value="Guest Post" ${backlink.linkType === 'Guest Post' ? 'selected' : ''}>Guest Post</option>
                        <option value="Directory" ${backlink.linkType === 'Directory' ? 'selected' : ''}>Directory</option>
                        <option value="Resource Page" ${backlink.linkType === 'Resource Page' ? 'selected' : ''}>Resource Page</option>
                        <option value="Forum" ${backlink.linkType === 'Forum' ? 'selected' : ''}>Forum</option>
                        <option value="Comment" ${backlink.linkType === 'Comment' ? 'selected' : ''}>Comment</option>
                        <option value="Social Media" ${backlink.linkType === 'Social Media' ? 'selected' : ''}>Social Media</option>
                        <option value="Other" ${backlink.linkType === 'Other' ? 'selected' : ''}>Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Status</label>
                    <select id="edit-backlink-status" class="form-input">
                        <option value="pending" ${backlink.status === 'pending' ? 'selected' : ''}>Pending</option>
                        <option value="active" ${backlink.status === 'active' ? 'selected' : ''}>Active</option>
                        <option value="broken" ${backlink.status === 'broken' ? 'selected' : ''}>Broken</option>
                    </select>
                </div>
            </div>
            <div class="form-actions">
                <button class="btn btn-secondary" onclick="closeEditBacklinkModal()">Cancel</button>
                <button class="btn btn-primary" onclick="updateBacklink(${id})">Update</button>
            </div>
        </div>
    `;
        document.body.appendChild(modal);
        modal.id = 'edit-backlink-modal';
    }

    // Close edit modal
    function closeEditBacklinkModal() {
        const modal = document.getElementById('edit-backlink-modal');
        if (modal) modal.remove();
    }

    // Update backlink
    function updateBacklink(id) {
        const index = backlinks.findIndex(b => b.id === id);
        if (index === -1) return;

        const source = document.getElementById('edit-backlink-source').value.trim();
        const url = document.getElementById('edit-backlink-url').value.trim();
        const type = document.getElementById('edit-backlink-type').value;
        const status = document.getElementById('edit-backlink-status').value;

        if (!source || !url) {
            alert('Please fill in all required fields');
            return;
        }

        backlinks[index] = {
            ...backlinks[index],
            sourceWebsite: source,
            url: url,
            linkType: type,
            status: status
        };

        saveBacklinks();
        closeEditBacklinkModal();
        alert('✅ Backlink updated successfully!');
    }

    // Delete backlink
    function deleteBacklink(id) {
        if (!confirm('Are you sure you want to delete this backlink?')) return;

        backlinks = backlinks.filter(b => b.id !== id);
        saveBacklinks();
        alert('✅ Backlink deleted successfully!');
    }

    // Initialize backlinks when view is shown
    document.addEventListener('DOMContentLoaded', function () {
        // Load backlinks on page load
        loadBacklinks();

        // Reload backlinks when switching to backlinks view
        document.querySelectorAll('[data-view="backlinks"]').forEach(el => {
            el.addEventListener('click', loadBacklinks);
        });
    });

})(); // End of IIFE - prevents global variable conflicts
