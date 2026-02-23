/**
 * Website Builder — Chat Interface
 * ChatGPT-style AI chat for editing websites.
 */
const PageBuilder = {
    state: {
        sessionId: null,
        siteSite: '',
        messages: [],
        sites: [],
        sessions: [],
        loading: false,
        uploading: false,
        pendingPlan: null,
        previewBranch: null,
        previewStatus: null, // null | 'creating' | 'ready' | 'deploying' | 'deployed'
        showSessions: false,
        deploys: [],
    },

    async render(company) {
        const el = document.getElementById('page-builder');
        if (!el) return;

        // Load sites
        try {
            this.state.sites = await API.get('/builder/sites');
            if (this.state.sites.length > 0 && !this.state.siteSite) {
                this.state.siteSite = this.state.sites[0].slug;
            }
        } catch (e) {
            this.state.sites = [
                { slug: 'us-exteriors', name: 'US Exteriors', available: true },
                { slug: 'us-drywall', name: 'US Drywall', available: true },
            ];
        }

        // Load sessions
        try {
            this.state.sessions = await API.get('/builder/sessions');
        } catch (e) {
            this.state.sessions = [];
        }

        el.innerHTML = this._html();
        this._bindEvents(el);
    },

    _html() {
        const { messages, sites, siteSite, loading, pendingPlan, previewStatus, previewBranch, showSessions, sessions, deploys } = this.state;

        const siteOptions = sites.map(s =>
            `<option value="${s.slug}" ${s.slug === siteSite ? 'selected' : ''}>${s.name}</option>`
        ).join('');

        const messagesHtml = messages.length === 0
            ? `<div class="empty-state" style="height:100%">
                 <div class="empty-state-icon"><i data-lucide="message-square"></i></div>
                 <p class="empty-state-title">What would you like to change?</p>
                 <p class="empty-state-text">Describe changes to your website and I'll help you make them.</p>
                 <div style="display:flex;gap:8px;margin-top:16px;flex-wrap:wrap;justify-content:center">
                   <button class="btn-secondary suggestion-chip" data-msg="Update the hero section heading">Update hero text</button>
                   <button class="btn-secondary suggestion-chip" data-msg="Add a new testimonial section">Add testimonials</button>
                   <button class="btn-secondary suggestion-chip" data-msg="Replace the project photos">Replace photos</button>
                 </div>
               </div>`
            : messages.map(m => this._messageBubble(m)).join('');

        const planHtml = pendingPlan ? this._planCard() : '';
        const previewHtml = previewStatus ? this._previewCard() : '';

        const sessionsList = showSessions && sessions.length > 0
            ? `<div class="builder-sessions-panel">
                 <div style="padding:12px 16px;border-bottom:1px solid var(--border-light);display:flex;justify-content:space-between;align-items:center">
                   <span style="font-size:13px;font-weight:600">Recent Sessions</span>
                   <button class="btn-ghost close-sessions" style="padding:2px"><i data-lucide="x" style="width:14px;height:14px"></i></button>
                 </div>
                 ${sessions.map(s => `
                   <div class="builder-session-item" data-session="${s.id}">
                     <div style="font-size:12px;font-weight:500;color:var(--text-primary)">${s.first_message || 'New session'}</div>
                     <div style="font-size:11px;color:var(--text-muted);margin-top:2px">${s.site_slug} · ${s.message_count} messages</div>
                   </div>
                 `).join('')}
               </div>`
            : '';

        return `
        <div class="builder-container">
          <!-- Header -->
          <div class="builder-header">
            <div style="display:flex;align-items:center;gap:12px;flex:1">
              <select class="builder-site-select" id="builder-site-select">${siteOptions}</select>
              <button class="btn-secondary" id="builder-new-session" style="padding:6px 12px;font-size:12px">
                <i data-lucide="plus" style="width:14px;height:14px"></i> New Chat
              </button>
              <button class="btn-ghost" id="builder-toggle-sessions" style="padding:6px 8px;font-size:12px">
                <i data-lucide="clock" style="width:14px;height:14px"></i> History
              </button>
            </div>
          </div>

          <div style="display:flex;flex:1;overflow:hidden;position:relative">
            <!-- Sessions Panel -->
            ${sessionsList}

            <!-- Chat Area -->
            <div class="builder-chat-area" id="builder-chat-area">
              <div class="builder-messages" id="builder-messages">
                ${messagesHtml}
                ${planHtml}
                ${previewHtml}
                ${loading ? '<div class="builder-typing"><span></span><span></span><span></span></div>' : ''}
              </div>

              <!-- File Drop Zone -->
              <div class="builder-dropzone" id="builder-dropzone" style="display:none">
                <i data-lucide="upload" style="width:24px;height:24px;color:var(--accent)"></i>
                <span>Drop images here</span>
              </div>

              <!-- Input -->
              <div class="builder-input-area">
                <div class="builder-input-wrapper">
                  <textarea id="builder-input" placeholder="Describe changes to your website..."
                    rows="1" ${loading ? 'disabled' : ''}></textarea>
                  <div style="display:flex;align-items:center;gap:4px">
                    <label class="btn-ghost builder-upload-btn" style="padding:6px;cursor:pointer">
                      <i data-lucide="paperclip" style="width:16px;height:16px"></i>
                      <input type="file" id="builder-file-input" multiple accept="image/*" style="display:none">
                    </label>
                    <button class="btn-primary" id="builder-send" style="padding:6px 12px" ${loading ? 'disabled' : ''}>
                      <i data-lucide="send" style="width:14px;height:14px"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>`;
    },

    _messageBubble(msg) {
        const isUser = msg.role === 'user';
        const align = isUser ? 'flex-end' : 'flex-start';
        const bgClass = isUser ? 'builder-msg-user' : 'builder-msg-ai';
        const content = isUser ? this._escapeHtml(msg.content) : this._renderMarkdown(msg.content);

        return `<div class="builder-msg" style="align-self:${align}">
          <div class="${bgClass}">${content}</div>
          <div style="font-size:10px;color:var(--text-muted);margin-top:2px;text-align:${isUser ? 'right' : 'left'}">
            ${msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : ''}
          </div>
        </div>`;
    },

    _planCard() {
        const plan = this.state.pendingPlan;
        if (!plan || !Array.isArray(plan)) return '';
        return `<div class="builder-plan-card">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
            <i data-lucide="file-edit" style="width:16px;height:16px;color:var(--accent)"></i>
            <span style="font-weight:600;font-size:14px">Proposed Changes</span>
          </div>
          <div style="margin-bottom:12px">
            ${plan.map(p => `<div style="padding:6px 0;border-bottom:1px solid var(--border-light);font-size:13px">
              <span class="mc-badge mc-badge-info" style="margin-right:8px">${p.action || 'edit'}</span>
              <code>${p.file || 'unknown'}</code>
              ${p.selector ? `<span style="color:var(--text-secondary);margin-left:8px">— ${p.selector}</span>` : ''}
            </div>`).join('')}
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn-primary" id="plan-approve">Approve & Preview</button>
            <button class="btn-secondary" id="plan-modify">Modify Request</button>
            <button class="btn-ghost" id="plan-cancel" style="color:var(--red)">Cancel</button>
          </div>
        </div>`;
    },

    _previewCard() {
        const { previewStatus, previewBranch } = this.state;
        const statusContent = {
            creating: '<div class="mc-spinner"></div><span>Creating preview...</span>',
            ready: `<span class="mc-badge mc-badge-success">Preview Ready</span>
                     <span style="font-size:12px;color:var(--text-secondary)">Branch: ${previewBranch}</span>`,
            deploying: '<div class="mc-spinner"></div><span>Deploying to live...</span>',
            deployed: '<span class="mc-badge mc-badge-success">Deployed!</span><span style="font-size:12px;color:var(--text-secondary)">Changes are live.</span>',
        }[previewStatus] || '';

        const actions = previewStatus === 'ready'
            ? `<div style="display:flex;gap:8px;margin-top:12px">
                 <button class="btn-primary" id="preview-deploy">Deploy to Live</button>
                 <button class="btn-ghost" id="preview-discard" style="color:var(--red)">Discard</button>
               </div>`
            : '';

        return `<div class="builder-preview-card">
          <div style="display:flex;align-items:center;gap:8px">${statusContent}</div>
          ${actions}
        </div>`;
    },

    _bindEvents(el) {
        const input = el.querySelector('#builder-input');
        const sendBtn = el.querySelector('#builder-send');
        const fileInput = el.querySelector('#builder-file-input');
        const siteSelect = el.querySelector('#builder-site-select');
        const newSession = el.querySelector('#builder-new-session');
        const toggleSessions = el.querySelector('#builder-toggle-sessions');

        // Send message
        const sendMessage = () => {
            const msg = input.value.trim();
            if (!msg || this.state.loading) return;
            input.value = '';
            input.style.height = 'auto';
            this._sendChat(msg);
        };

        if (sendBtn) sendBtn.addEventListener('click', sendMessage);
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            // Auto-resize
            input.addEventListener('input', () => {
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            });
        }

        // File upload
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                for (const file of e.target.files) {
                    this._uploadFile(file);
                }
                e.target.value = '';
            });
        }

        // Site selector
        if (siteSelect) {
            siteSelect.addEventListener('change', (e) => {
                this.state.siteSite = e.target.value;
                this.state.sessionId = null;
                this.state.messages = [];
                this.state.pendingPlan = null;
                this.state.previewStatus = null;
                this.render();
            });
        }

        // New session
        if (newSession) {
            newSession.addEventListener('click', () => {
                this.state.sessionId = null;
                this.state.messages = [];
                this.state.pendingPlan = null;
                this.state.previewStatus = null;
                this.render();
            });
        }

        // Toggle sessions
        if (toggleSessions) {
            toggleSessions.addEventListener('click', () => {
                this.state.showSessions = !this.state.showSessions;
                this.render();
            });
        }

        // Close sessions
        const closeBtn = el.querySelector('.close-sessions');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.state.showSessions = false;
                this.render();
            });
        }

        // Session items
        el.querySelectorAll('.builder-session-item').forEach(item => {
            item.addEventListener('click', () => this._loadSession(item.dataset.session));
        });

        // Suggestion chips
        el.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                if (input) input.value = chip.dataset.msg;
                sendMessage();
            });
        });

        // Plan buttons
        const approveBtn = el.querySelector('#plan-approve');
        const modifyBtn = el.querySelector('#plan-modify');
        const cancelBtn = el.querySelector('#plan-cancel');
        if (approveBtn) approveBtn.addEventListener('click', () => this._createPreview());
        if (modifyBtn) modifyBtn.addEventListener('click', () => {
            this.state.pendingPlan = null;
            this.render();
            if (input) input.focus();
        });
        if (cancelBtn) cancelBtn.addEventListener('click', () => {
            this.state.pendingPlan = null;
            this.render();
        });

        // Preview buttons
        const deployBtn = el.querySelector('#preview-deploy');
        const discardBtn = el.querySelector('#preview-discard');
        if (deployBtn) deployBtn.addEventListener('click', () => this._deploy());
        if (discardBtn) discardBtn.addEventListener('click', () => this._discard());

        // Drag and drop
        const chatArea = el.querySelector('#builder-chat-area');
        const dropzone = el.querySelector('#builder-dropzone');
        if (chatArea && dropzone) {
            chatArea.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.style.display = 'flex'; });
            chatArea.addEventListener('dragleave', (e) => {
                if (!chatArea.contains(e.relatedTarget)) dropzone.style.display = 'none';
            });
            chatArea.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.style.display = 'none';
                for (const file of e.dataTransfer.files) this._uploadFile(file);
            });
        }

        // Lucide icons
        if (window.lucide) lucide.createIcons();
    },

    async _sendChat(message) {
        this.state.messages.push({ role: 'user', content: message, timestamp: new Date().toISOString() });
        this.state.loading = true;
        this.render();
        this._scrollToBottom();

        try {
            const resp = await API.post('/builder/chat', {
                session_id: this.state.sessionId,
                message,
                site_slug: this.state.siteSite,
            });

            this.state.sessionId = resp.session_id;
            this.state.messages.push({ role: 'assistant', content: resp.response, timestamp: new Date().toISOString() });
            if (resp.plan) this.state.pendingPlan = resp.plan;
        } catch (e) {
            this.state.messages.push({ role: 'assistant', content: 'Sorry, something went wrong. Please try again.', timestamp: new Date().toISOString() });
        }

        this.state.loading = false;
        this.render();
        this._scrollToBottom();
    },

    async _uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', this.state.sessionId || 'new');

        try {
            const resp = await fetch('/api/builder/upload', { method: 'POST', body: formData });
            if (!resp.ok) throw new Error('Upload failed');
            const data = await resp.json();
            this.state.messages.push({ role: 'user', content: `Uploaded: ${file.name}`, timestamp: new Date().toISOString() });
            this.render();
        } catch (e) {
            this.state.messages.push({ role: 'assistant', content: `Failed to upload ${file.name}. ${e.message}`, timestamp: new Date().toISOString() });
            this.render();
        }
    },

    async _loadSession(sessionId) {
        try {
            const session = await API.get(`/builder/sessions/${sessionId}`);
            this.state.sessionId = session.id;
            this.state.siteSite = session.site_slug;
            this.state.messages = session.messages || [];
            this.state.pendingPlan = session.proposed_changes;
            this.state.showSessions = false;
            this.render();
        } catch (e) {
            console.error('Failed to load session:', e);
        }
    },

    async _createPreview() {
        this.state.previewStatus = 'creating';
        this.render();

        try {
            const resp = await API.post('/builder/preview', { session_id: this.state.sessionId });
            if (resp.status === 'error') {
                this.state.messages.push({ role: 'assistant', content: `Preview failed: ${resp.errors?.join(', ')}`, timestamp: new Date().toISOString() });
                this.state.previewStatus = null;
            } else {
                this.state.previewBranch = resp.branch_name;
                this.state.previewStatus = 'ready';
                this.state.pendingPlan = null;
            }
        } catch (e) {
            this.state.messages.push({ role: 'assistant', content: 'Failed to create preview. Please try again.', timestamp: new Date().toISOString() });
            this.state.previewStatus = null;
        }

        this.render();
    },

    async _deploy() {
        if (!confirm('Deploy changes to live? This will update the live website.')) return;

        this.state.previewStatus = 'deploying';
        this.render();

        try {
            await API.post('/builder/deploy', {
                session_id: this.state.sessionId,
                branch_name: this.state.previewBranch,
            });
            this.state.previewStatus = 'deployed';
            this.state.messages.push({ role: 'assistant', content: 'Changes deployed successfully! Your website will update in ~30 seconds.', timestamp: new Date().toISOString() });
        } catch (e) {
            this.state.messages.push({ role: 'assistant', content: 'Deploy failed. Please try again.', timestamp: new Date().toISOString() });
            this.state.previewStatus = 'ready';
        }

        this.render();
    },

    async _discard() {
        if (!confirm('Discard preview? No changes will be made.')) return;

        try {
            await API.post('/builder/discard', {
                session_id: this.state.sessionId,
                branch_name: this.state.previewBranch,
            });
        } catch (e) { /* non-critical */ }

        this.state.previewStatus = null;
        this.state.previewBranch = null;
        this.state.pendingPlan = null;
        this.render();
    },

    _scrollToBottom() {
        const el = document.getElementById('builder-messages');
        if (el) setTimeout(() => el.scrollTop = el.scrollHeight, 50);
    },

    _escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },

    _renderMarkdown(text) {
        // Escape HTML first to prevent XSS, then apply markdown formatting
        return this._escapeHtml(text)
            .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="builder-code"><code>$2</code></pre>')
            .replace(/`([^`]+)`/g, '<code class="builder-inline-code">$1</code>')
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/^### (.+)$/gm, '<h4 style="font-size:13px;font-weight:600;margin:8px 0 4px">$1</h4>')
            .replace(/^## (.+)$/gm, '<h3 style="font-size:14px;font-weight:600;margin:8px 0 4px">$1</h3>')
            .replace(/^- (.+)$/gm, '<div style="padding-left:12px">• $1</div>')
            .replace(/\n/g, '<br>');
    },
};

window.PageBuilder = PageBuilder;
