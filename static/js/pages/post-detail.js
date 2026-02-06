/**
 * Mission Control — Post Detail Page
 * Displays individual post details with editing, approval, and scheduling controls.
 */
window.PagePostDetail = {
    container: null,

    async render(postId) {
        this.container = document.getElementById('page-post-detail');
        if (!this.container) return;

        if (!postId) {
            this.container.innerHTML = this._renderEmpty();
            if (window.lucide) lucide.createIcons();
            return;
        }

        this.container.innerHTML = this._renderLoading();
        if (window.lucide) lucide.createIcons();

        try {
            const post = await API.posts.get(postId);
            this.container.innerHTML = this._renderPost(post);
            if (window.lucide) lucide.createIcons();
            this._bindEvents(post);
        } catch (err) {
            console.error('PagePostDetail load error:', err);
            this.container.innerHTML = this._renderError(err.message);
            if (window.lucide) lucide.createIcons();
        }
    },

    _renderEmpty() {
        return `
            <div class="flex flex-col items-center justify-center py-24 text-gray-400">
                <i data-lucide="file-text" class="w-16 h-16 mb-4 opacity-50"></i>
                <p class="text-lg font-medium text-gray-500">Select a post from the calendar</p>
                <p class="text-sm mt-1">Click any post on the <a href="#calendar" class="text-sky hover:underline">LinkedIn Calendar</a> to view details.</p>
            </div>
        `;
    },

    _renderLoading() {
        return `
            <div class="flex items-center justify-center py-24">
                <div class="mc-spinner"></div>
                <span class="ml-3 text-sm text-gray-500">Loading post details...</span>
            </div>
        `;
    },

    _renderError(message) {
        return `
            <div class="flex flex-col items-center justify-center py-24 text-red-400">
                <i data-lucide="alert-circle" class="w-12 h-12 mb-3"></i>
                <p class="text-sm font-medium text-red-600">Failed to load post</p>
                <p class="text-xs text-red-400 mt-1">${this._esc(message)}</p>
                <a href="#calendar" class="mt-4 text-sm text-sky hover:underline">Back to Calendar</a>
            </div>
        `;
    },

    _renderPost(post) {
        const companyColor = this._companyColor(post.company_slug);
        const statusClass = 'badge badge-' + (post.status || 'draft');
        const scheduledDate = post.scheduled_date ? new Date(post.scheduled_date).toLocaleDateString('en-US', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
        }) : 'Not scheduled';
        const createdDate = post.created_at ? new Date(post.created_at).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        }) : '';
        const hashtags = (post.hashtags || []);
        const engagement = post.engagement || {};
        const isPublished = post.status === 'published';
        const isDraft = post.status === 'draft';
        const isScheduled = post.status === 'scheduled';
        const isReview = post.status === 'review';

        return `
            <!-- Back button -->
            <div class="mb-4">
                <a href="#calendar" class="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-navy transition-colors" id="pd-back-btn">
                    <i data-lucide="arrow-left" class="w-4 h-4"></i>
                    Back to Calendar
                </a>
            </div>

            <!-- Post Header -->
            <div class="mc-card mb-6">
                <div class="mc-card-header">
                    <div class="flex items-center gap-3">
                        <span class="company-dot" style="background:${companyColor}"></span>
                        <span class="text-sm text-gray-600">${this._esc(post.company || '')}</span>
                        <span class="text-gray-300">|</span>
                        <span class="${statusClass}">${this._esc(post.status || 'draft')}</span>
                    </div>
                    <div class="flex items-center gap-2 text-xs text-gray-400">
                        <i data-lucide="linkedin" class="w-3.5 h-3.5"></i>
                        <span>${this._esc(post.platform || 'LinkedIn')}</span>
                    </div>
                </div>
                <div class="mc-card-body">
                    <h2 class="text-xl font-display font-semibold text-navy mb-2">${this._esc(post.title || 'Untitled Post')}</h2>
                    <div class="flex items-center gap-4 text-xs text-gray-500">
                        <span class="flex items-center gap-1">
                            <i data-lucide="calendar" class="w-3.5 h-3.5"></i>
                            ${this._esc(scheduledDate)}
                        </span>
                        ${createdDate ? `<span class="flex items-center gap-1"><i data-lucide="clock" class="w-3.5 h-3.5"></i> Created ${this._esc(createdDate)}</span>` : ''}
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Content Preview + Editor (left 2 cols) -->
                <div class="lg:col-span-2 space-y-6">
                    <!-- Content Card -->
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="text-sm font-semibold text-navy">Post Content</h3>
                            <button id="pd-toggle-edit" class="text-xs text-sky hover:text-sky/80 font-medium transition-colors">
                                <i data-lucide="pencil" class="w-3.5 h-3.5 inline mr-1"></i> Edit
                            </button>
                        </div>
                        <div class="mc-card-body">
                            <!-- View mode -->
                            <div id="pd-content-view">
                                <div class="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap leading-relaxed">${this._esc(post.content || 'No content yet.')}</div>
                                ${hashtags.length > 0 ? `
                                    <div class="flex flex-wrap gap-2 mt-4 pt-4 border-t border-gray-100">
                                        ${hashtags.map(tag => `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-sky/10 text-sky">#${this._esc(tag)}</span>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                            <!-- Edit mode (hidden initially) -->
                            <div id="pd-content-edit" class="hidden">
                                <textarea id="pd-content-textarea"
                                    class="w-full h-48 border border-gray-300 rounded-lg p-3 text-sm text-gray-700 focus:ring-2 focus:ring-sky/30 focus:border-sky outline-none resize-y font-body"
                                    placeholder="Write your post content...">${this._esc(post.content || '')}</textarea>
                                <div class="flex items-center justify-between mt-3">
                                    <span id="pd-save-feedback" class="text-xs text-gray-400"></span>
                                    <div class="flex gap-2">
                                        <button id="pd-cancel-edit" class="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg transition-colors">
                                            Cancel
                                        </button>
                                        <button id="pd-save-content" class="px-4 py-1.5 text-xs text-white bg-sky hover:bg-sky/90 rounded-lg font-medium transition-colors">
                                            <i data-lucide="save" class="w-3.5 h-3.5 inline mr-1"></i> Save
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Engagement Stats (only if published) -->
                    ${isPublished ? `
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="text-sm font-semibold text-navy">Engagement</h3>
                        </div>
                        <div class="mc-card-body">
                            <div class="grid grid-cols-3 gap-4">
                                <div class="text-center p-4 rounded-lg bg-blue-50">
                                    <div class="flex items-center justify-center mb-2">
                                        <i data-lucide="thumbs-up" class="w-5 h-5 text-blue-500"></i>
                                    </div>
                                    <div class="text-2xl font-bold text-navy">${engagement.likes || 0}</div>
                                    <div class="text-xs text-gray-500 uppercase tracking-wide mt-1">Likes</div>
                                </div>
                                <div class="text-center p-4 rounded-lg bg-green-50">
                                    <div class="flex items-center justify-center mb-2">
                                        <i data-lucide="message-circle" class="w-5 h-5 text-green-500"></i>
                                    </div>
                                    <div class="text-2xl font-bold text-navy">${engagement.comments || 0}</div>
                                    <div class="text-xs text-gray-500 uppercase tracking-wide mt-1">Comments</div>
                                </div>
                                <div class="text-center p-4 rounded-lg bg-purple-50">
                                    <div class="flex items-center justify-center mb-2">
                                        <i data-lucide="share-2" class="w-5 h-5 text-purple-500"></i>
                                    </div>
                                    <div class="text-2xl font-bold text-navy">${engagement.shares || 0}</div>
                                    <div class="text-xs text-gray-500 uppercase tracking-wide mt-1">Shares</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>

                <!-- Actions Sidebar (right col) -->
                <div class="space-y-6">
                    <!-- Actions Card -->
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="text-sm font-semibold text-navy">Actions</h3>
                        </div>
                        <div class="mc-card-body space-y-3">
                            ${isDraft || isReview ? `
                                <button id="pd-approve-btn" class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors">
                                    <i data-lucide="check-circle" class="w-4 h-4"></i>
                                    Approve
                                </button>
                                <button id="pd-reject-btn" class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors">
                                    <i data-lucide="x-circle" class="w-4 h-4"></i>
                                    Reject
                                </button>
                            ` : ''}
                            ${isScheduled ? `
                                <button id="pd-reschedule-btn" class="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-sky hover:bg-sky/90 text-white rounded-lg text-sm font-medium transition-colors">
                                    <i data-lucide="calendar-clock" class="w-4 h-4"></i>
                                    Reschedule
                                </button>
                            ` : ''}
                            <a href="#calendar" class="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 text-gray-600 hover:bg-gray-50 rounded-lg text-sm font-medium transition-colors">
                                <i data-lucide="arrow-left" class="w-4 h-4"></i>
                                Back to Calendar
                            </a>
                        </div>
                    </div>

                    <!-- Post Meta Card -->
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="text-sm font-semibold text-navy">Details</h3>
                        </div>
                        <div class="mc-card-body">
                            <dl class="space-y-3 text-sm">
                                <div class="flex justify-between">
                                    <dt class="text-gray-500">Post ID</dt>
                                    <dd class="font-mono text-xs text-gray-700">${this._esc(String(post.id))}</dd>
                                </div>
                                <div class="flex justify-between">
                                    <dt class="text-gray-500">Status</dt>
                                    <dd><span class="${statusClass}">${this._esc(post.status || 'draft')}</span></dd>
                                </div>
                                <div class="flex justify-between">
                                    <dt class="text-gray-500">Platform</dt>
                                    <dd class="text-gray-700">${this._esc(post.platform || 'LinkedIn')}</dd>
                                </div>
                                <div class="flex justify-between">
                                    <dt class="text-gray-500">Company</dt>
                                    <dd class="flex items-center gap-1.5">
                                        <span class="company-dot" style="background:${companyColor}"></span>
                                        <span class="text-gray-700">${this._esc(post.company || '')}</span>
                                    </dd>
                                </div>
                                ${post.scheduled_date ? `
                                <div class="flex justify-between">
                                    <dt class="text-gray-500">Scheduled</dt>
                                    <dd class="text-gray-700">${new Date(post.scheduled_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</dd>
                                </div>
                                ` : ''}
                                ${hashtags.length > 0 ? `
                                <div>
                                    <dt class="text-gray-500 mb-1.5">Hashtags</dt>
                                    <dd class="flex flex-wrap gap-1">
                                        ${hashtags.map(tag => `<span class="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600">#${this._esc(tag)}</span>`).join('')}
                                    </dd>
                                </div>
                                ` : ''}
                            </dl>
                        </div>
                    </div>

                    <!-- Action Feedback -->
                    <div id="pd-action-feedback" class="hidden mc-card">
                        <div class="mc-card-body text-center py-3">
                            <span id="pd-action-msg" class="text-sm"></span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    _bindEvents(post) {
        const container = this.container;

        // Toggle edit mode
        const toggleBtn = container.querySelector('#pd-toggle-edit');
        const viewEl = container.querySelector('#pd-content-view');
        const editEl = container.querySelector('#pd-content-edit');
        const textarea = container.querySelector('#pd-content-textarea');

        if (toggleBtn && viewEl && editEl) {
            toggleBtn.addEventListener('click', () => {
                const isEditing = !editEl.classList.contains('hidden');
                if (isEditing) {
                    editEl.classList.add('hidden');
                    viewEl.classList.remove('hidden');
                    toggleBtn.innerHTML = '<i data-lucide="pencil" class="w-3.5 h-3.5 inline mr-1"></i> Edit';
                } else {
                    viewEl.classList.add('hidden');
                    editEl.classList.remove('hidden');
                    toggleBtn.innerHTML = '<i data-lucide="eye" class="w-3.5 h-3.5 inline mr-1"></i> View';
                    if (textarea) textarea.focus();
                }
                if (window.lucide) lucide.createIcons();
            });
        }

        // Cancel edit
        const cancelBtn = container.querySelector('#pd-cancel-edit');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                if (textarea) textarea.value = post.content || '';
                editEl.classList.add('hidden');
                viewEl.classList.remove('hidden');
                toggleBtn.innerHTML = '<i data-lucide="pencil" class="w-3.5 h-3.5 inline mr-1"></i> Edit';
                if (window.lucide) lucide.createIcons();
            });
        }

        // Save content
        const saveBtn = container.querySelector('#pd-save-content');
        const feedbackEl = container.querySelector('#pd-save-feedback');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                const newContent = textarea ? textarea.value : '';
                saveBtn.disabled = true;
                saveBtn.textContent = 'Saving...';
                try {
                    await API.posts.update(post.id, { content: newContent });
                    if (feedbackEl) {
                        feedbackEl.textContent = 'Saved successfully';
                        feedbackEl.className = 'text-xs text-green-600';
                    }
                    // Update the view content
                    const viewContent = viewEl.querySelector('.prose');
                    if (viewContent) viewContent.textContent = newContent;
                    post.content = newContent;
                    // Switch back to view mode after a brief pause
                    setTimeout(() => {
                        editEl.classList.add('hidden');
                        viewEl.classList.remove('hidden');
                        toggleBtn.innerHTML = '<i data-lucide="pencil" class="w-3.5 h-3.5 inline mr-1"></i> Edit';
                        if (feedbackEl) feedbackEl.textContent = '';
                        if (window.lucide) lucide.createIcons();
                    }, 1000);
                } catch (err) {
                    if (feedbackEl) {
                        feedbackEl.textContent = 'Save failed: ' + err.message;
                        feedbackEl.className = 'text-xs text-red-600';
                    }
                } finally {
                    saveBtn.disabled = false;
                    saveBtn.innerHTML = '<i data-lucide="save" class="w-3.5 h-3.5 inline mr-1"></i> Save';
                    if (window.lucide) lucide.createIcons();
                }
            });
        }

        // Approve button
        const approveBtn = container.querySelector('#pd-approve-btn');
        if (approveBtn) {
            approveBtn.addEventListener('click', async () => {
                approveBtn.disabled = true;
                approveBtn.textContent = 'Approving...';
                try {
                    await API.posts.approve(post.id);
                    this._showFeedback('Post approved successfully', 'text-green-600');
                    // Re-render with updated data
                    await this.render(post.id);
                } catch (err) {
                    this._showFeedback('Failed to approve: ' + err.message, 'text-red-600');
                    approveBtn.disabled = false;
                    approveBtn.innerHTML = '<i data-lucide="check-circle" class="w-4 h-4"></i> Approve';
                    if (window.lucide) lucide.createIcons();
                }
            });
        }

        // Reject button
        const rejectBtn = container.querySelector('#pd-reject-btn');
        if (rejectBtn) {
            rejectBtn.addEventListener('click', async () => {
                rejectBtn.disabled = true;
                rejectBtn.textContent = 'Rejecting...';
                try {
                    await API.posts.reject(post.id);
                    this._showFeedback('Post rejected', 'text-red-600');
                    await this.render(post.id);
                } catch (err) {
                    this._showFeedback('Failed to reject: ' + err.message, 'text-red-600');
                    rejectBtn.disabled = false;
                    rejectBtn.innerHTML = '<i data-lucide="x-circle" class="w-4 h-4"></i> Reject';
                    if (window.lucide) lucide.createIcons();
                }
            });
        }

        // Reschedule button
        const rescheduleBtn = container.querySelector('#pd-reschedule-btn');
        if (rescheduleBtn) {
            rescheduleBtn.addEventListener('click', async () => {
                const currentDate = post.scheduled_date ? post.scheduled_date.split('T')[0] : '';
                const newDate = prompt('Enter new scheduled date (YYYY-MM-DD):', currentDate);
                if (!newDate) return;
                // Validate date format
                if (!/^\d{4}-\d{2}-\d{2}$/.test(newDate)) {
                    this._showFeedback('Invalid date format. Use YYYY-MM-DD.', 'text-red-600');
                    return;
                }
                rescheduleBtn.disabled = true;
                rescheduleBtn.textContent = 'Rescheduling...';
                try {
                    await API.posts.reschedule(post.id, newDate);
                    this._showFeedback('Post rescheduled to ' + newDate, 'text-sky');
                    await this.render(post.id);
                } catch (err) {
                    this._showFeedback('Failed to reschedule: ' + err.message, 'text-red-600');
                    rescheduleBtn.disabled = false;
                    rescheduleBtn.innerHTML = '<i data-lucide="calendar-clock" class="w-4 h-4"></i> Reschedule';
                    if (window.lucide) lucide.createIcons();
                }
            });
        }
    },

    _showFeedback(message, colorClass) {
        const fb = this.container.querySelector('#pd-action-feedback');
        const msg = this.container.querySelector('#pd-action-msg');
        if (fb && msg) {
            msg.textContent = message;
            msg.className = 'text-sm ' + colorClass;
            fb.classList.remove('hidden');
            setTimeout(() => fb.classList.add('hidden'), 4000);
        }
    },

    _companyColor(slug) {
        const colors = {
            'us-framing': '#4A90D9',
            'us-drywall': '#B8860B',
            'us-exteriors': '#2D5F2D',
            'us-development': '#C4AF94',
        };
        return colors[slug] || '#6B7280';
    },

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
};
