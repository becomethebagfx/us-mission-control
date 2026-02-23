/**
 * Monday Morning Brief — Weekly AI-Generated Summary
 */
const PageBrief = {
    state: {
        latest: null,
        history: [],
        loading: false,
        generating: false,
        view: 'latest', // 'latest' | 'history'
    },

    async render(company) {
        const el = document.getElementById('page-brief');
        if (!el) return;

        this.state.loading = true;
        el.innerHTML = '<div class="mc-card"><div class="mc-card-body"><div class="skeleton skeleton-card"></div></div></div>';

        try {
            const [latest, history] = await Promise.all([
                API.get('/brief/latest'),
                API.get('/brief/history'),
            ]);
            this.state.latest = latest.brief !== undefined ? latest.brief : latest;
            this.state.history = history;
        } catch (e) {
            console.error('Failed to load briefs:', e);
        }

        this.state.loading = false;
        el.innerHTML = this._html();
        this._bindEvents(el);
        if (window.lucide) lucide.createIcons();
    },

    /** Render brief summary card for the Dashboard home page */
    renderDashboardCard() {
        const brief = this.state.latest;
        if (!brief) {
            return `<div class="mc-card" style="margin-bottom:16px">
              <div class="mc-card-header">
                <h3><i data-lucide="newspaper" style="width:14px;height:14px;margin-right:6px"></i>Weekly Brief</h3>
                <button class="btn-ghost generate-brief-btn" style="font-size:12px">
                  <i data-lucide="sparkles" style="width:12px;height:12px"></i> Generate Now
                </button>
              </div>
              <div class="mc-card-body">
                <p style="font-size:13px;color:var(--text-secondary)">No brief generated yet. Click "Generate Now" to create your first weekly summary.</p>
              </div>
            </div>`;
        }

        const status = brief.status_at_glance || {};
        const sections = brief.sections || {};

        return `<div class="mc-card" style="margin-bottom:16px">
          <div class="mc-card-header">
            <h3><i data-lucide="newspaper" style="width:14px;height:14px;margin-right:6px"></i>Weekly Brief</h3>
            <div style="display:flex;align-items:center;gap:8px">
              ${Object.entries(status).map(([slug, color]) =>
                `<div style="display:flex;align-items:center;gap:4px">
                   <div class="brief-status-dot brief-dot-${color}"></div>
                   <span style="font-size:11px;color:var(--text-secondary)">${slug.replace('us-','').replace('-',' ')}</span>
                 </div>`
              ).join('')}
              <a href="#brief" class="btn-ghost" style="font-size:12px">Read Full Brief →</a>
            </div>
          </div>
          <div class="mc-card-body">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
              <div>
                <div style="font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">Activity</div>
                <p style="font-size:13px">${sections.activity?.description || 'No activity data'}</p>
              </div>
              <div>
                <div style="font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">AI Insight</div>
                <p style="font-size:13px;color:var(--accent)">${sections.insight || 'No insight available'}</p>
              </div>
            </div>
            ${sections.action_items?.length ? `
              <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border-light)">
                <div style="font-size:12px;font-weight:600;color:var(--text-secondary);margin-bottom:4px">Action Items</div>
                ${sections.action_items.map(item => `
                  <div style="display:flex;align-items:center;gap:6px;font-size:12px;padding:2px 0">
                    <i data-lucide="circle" style="width:10px;height:10px;color:var(--orange)"></i>
                    ${item}
                  </div>
                `).join('')}
              </div>
            ` : ''}
            <div style="margin-top:8px;font-size:11px;color:var(--text-muted)">
              Generated: ${brief.generated_at ? new Date(brief.generated_at).toLocaleDateString('en-US', { weekday:'long', month:'short', day:'numeric', hour:'numeric', minute:'2-digit' }) : 'N/A'}
            </div>
          </div>
        </div>`;
    },

    _html() {
        const { latest, history, view, generating } = this.state;

        const tabs = `<div class="mc-tabs">
          <div class="mc-tab ${view === 'latest' ? 'mc-tab-active' : 'mc-tab-inactive'}" data-view="latest">Latest Brief</div>
          <div class="mc-tab ${view === 'history' ? 'mc-tab-active' : 'mc-tab-inactive'}" data-view="history">History</div>
        </div>`;

        if (view === 'history') {
            return `${tabs}${this._historyView()}`;
        }

        if (!latest) {
            return `${tabs}
            <div class="mc-card">
              <div class="mc-card-body empty-state">
                <div class="empty-state-icon"><i data-lucide="newspaper"></i></div>
                <p class="empty-state-title">No Brief Yet</p>
                <p class="empty-state-text">Generate your first Monday Morning Brief to see a weekly summary of your website performance.</p>
                <button class="btn-primary generate-brief-btn" style="margin-top:16px" ${generating ? 'disabled' : ''}>
                  ${generating ? '<div class="mc-spinner" style="width:14px;height:14px"></div>' : '<i data-lucide="sparkles" style="width:14px;height:14px"></i>'} Generate Brief
                </button>
              </div>
            </div>`;
        }

        return `${tabs}${this._briefDetailView(latest)}`;
    },

    _briefDetailView(brief) {
        const status = brief.status_at_glance || {};
        const sections = brief.sections || {};

        return `
        <!-- Status at a Glance -->
        <div class="mc-card" style="margin-bottom:16px">
          <div class="mc-card-header">
            <h3>Status at a Glance</h3>
            <button class="btn-ghost generate-brief-btn" style="font-size:12px" ${this.state.generating ? 'disabled' : ''}>
              ${this.state.generating ? '<div class="mc-spinner" style="width:12px;height:12px"></div>' : '<i data-lucide="refresh-cw" style="width:12px;height:12px"></i>'} Regenerate
            </button>
          </div>
          <div class="mc-card-body">
            <div style="display:flex;gap:24px;flex-wrap:wrap">
              ${Object.entries(status).map(([slug, color]) => `
                <div style="display:flex;align-items:center;gap:10px">
                  <div class="brief-status-dot-lg brief-dot-${color}"></div>
                  <div>
                    <div style="font-size:14px;font-weight:600">${slug.replace('us-','US ').replace(/(^\w|\s\w)/g, m => m.toUpperCase())}</div>
                    <div style="font-size:12px;color:var(--text-secondary)">${color === 'green' ? 'All systems go' : color === 'yellow' ? 'Needs attention' : 'Issues detected'}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Activity -->
        <div class="mc-card" style="margin-bottom:16px">
          <div class="mc-card-header"><h3>This Week's Activity</h3></div>
          <div class="mc-card-body">
            <p style="font-size:14px;line-height:1.6">${sections.activity?.description || 'No activity data available.'}</p>
          </div>
        </div>

        <!-- Performance -->
        <div class="mc-card" style="margin-bottom:16px">
          <div class="mc-card-header"><h3>Performance</h3></div>
          <div class="mc-card-body">
            <p style="font-size:14px;line-height:1.6">${sections.performance?.description || 'No performance data available.'}</p>
          </div>
        </div>

        <!-- AI Insight -->
        <div class="mc-card" style="margin-bottom:16px;border-left:3px solid var(--accent)">
          <div class="mc-card-header"><h3><i data-lucide="lightbulb" style="width:14px;height:14px;margin-right:6px;color:var(--accent)"></i>AI Insight</h3></div>
          <div class="mc-card-body">
            <p style="font-size:14px;line-height:1.6;color:var(--accent)">${sections.insight || 'No insight available.'}</p>
          </div>
        </div>

        <!-- Action Items -->
        ${sections.action_items?.length ? `
        <div class="mc-card" style="margin-bottom:16px">
          <div class="mc-card-header"><h3>Action Items</h3></div>
          <div class="mc-card-body">
            ${sections.action_items.map((item, i) => `
              <div style="display:flex;align-items:start;gap:10px;padding:8px 0;${i > 0 ? 'border-top:1px solid var(--border-light)' : ''}">
                <div style="width:20px;height:20px;border:2px solid var(--border);border-radius:4px;flex-shrink:0;margin-top:1px"></div>
                <span style="font-size:14px">${item}</span>
              </div>
            `).join('')}
          </div>
        </div>` : ''}

        <div style="font-size:12px;color:var(--text-muted);text-align:center;padding:8px">
          Week of ${brief.week_of || 'N/A'} · Generated ${brief.generated_at ? new Date(brief.generated_at).toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric', hour:'numeric', minute:'2-digit' }) : 'N/A'}
        </div>`;
    },

    _historyView() {
        const history = this.state.history;
        if (!history || history.length === 0) {
            return '<div class="mc-card"><div class="mc-card-body empty-state"><p class="empty-state-text">No brief history yet.</p></div></div>';
        }

        return `<div class="mc-card">
          <div class="mc-card-body">
            <table class="mc-table">
              <thead><tr><th>Week</th><th>Status</th><th>Generated</th></tr></thead>
              <tbody>
                ${history.map(b => {
                    const status = b.status_at_glance || {};
                    const dots = Object.entries(status).map(([s, c]) =>
                        `<div class="brief-status-dot brief-dot-${c}" title="${s}"></div>`
                    ).join('');
                    return `<tr class="history-row" data-week="${b.week_of}">
                      <td style="font-weight:500">${b.week_of}</td>
                      <td><div style="display:flex;gap:4px">${dots}</div></td>
                      <td style="font-size:12px;color:var(--text-secondary)">${b.generated_at ? new Date(b.generated_at).toLocaleDateString() : ''}</td>
                    </tr>`;
                }).join('')}
              </tbody>
            </table>
          </div>
        </div>`;
    },

    _bindEvents(el) {
        // Tab switching
        el.querySelectorAll('.mc-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.state.view = tab.dataset.view;
                el.innerHTML = this._html();
                this._bindEvents(el);
                if (window.lucide) lucide.createIcons();
            });
        });

        // Generate button
        el.querySelectorAll('.generate-brief-btn').forEach(btn => {
            btn.addEventListener('click', () => this._generateBrief());
        });
    },

    async _generateBrief() {
        this.state.generating = true;
        const el = document.getElementById('page-brief');
        if (el) { el.innerHTML = this._html(); this._bindEvents(el); if (window.lucide) lucide.createIcons(); }

        try {
            const brief = await API.post('/brief/generate');
            this.state.latest = brief;
            this.state.view = 'latest';
        } catch (e) {
            console.error('Failed to generate brief:', e);
        }

        this.state.generating = false;
        if (el) { el.innerHTML = this._html(); this._bindEvents(el); if (window.lucide) lucide.createIcons(); }
    },
};

window.PageBrief = PageBrief;
