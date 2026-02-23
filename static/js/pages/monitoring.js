/**
 * Monitoring — Deployments, Performance, Logs, Analytics
 */
const PageMonitoring = {
    state: {
        tab: 'deploys',
        range: '24h',
        site: '',
        deploys: [],
        performance: null,
        logs: [],
        metrics: null,
        loading: false,
    },

    async render(company) {
        const el = document.getElementById('page-monitoring');
        if (!el) return;

        this.state.site = company || '';
        this.state.loading = true;
        el.innerHTML = this._loadingHtml();

        await this._loadData();

        this.state.loading = false;
        el.innerHTML = this._html();
        this._bindEvents(el);
        if (window.lucide) lucide.createIcons();
    },

    async _loadData() {
        const { tab, range, site } = this.state;
        const params = {};
        if (site) params.site = site;
        if (range) params.range = range;

        try {
            switch (tab) {
                case 'deploys':
                    this.state.deploys = await API.get('/monitoring/deploys', params);
                    break;
                case 'performance':
                    this.state.performance = await API.get('/monitoring/performance', params);
                    break;
                case 'logs':
                    this.state.logs = await API.get('/monitoring/logs', params);
                    break;
                case 'analytics':
                    this.state.metrics = await API.get('/monitoring/metrics', params);
                    break;
            }
        } catch (e) {
            console.error('Failed to load monitoring data:', e);
        }
    },

    _loadingHtml() {
        return `<div class="mc-card"><div class="mc-card-body"><div class="skeleton skeleton-card"></div></div></div>`;
    },

    _html() {
        const { tab, range } = this.state;
        const tabs = [
            { id: 'deploys', label: 'Deployments', icon: 'rocket' },
            { id: 'performance', label: 'Performance', icon: 'gauge' },
            { id: 'logs', label: 'Logs', icon: 'terminal' },
            { id: 'analytics', label: 'Analytics', icon: 'bar-chart-3' },
        ];

        const ranges = ['6h', '24h', '3d', '7d', '30d'];

        return `
        <!-- Tabs -->
        <div class="mc-tabs">
          ${tabs.map(t => `
            <div class="mc-tab ${tab === t.id ? 'mc-tab-active' : 'mc-tab-inactive'}" data-tab="${t.id}">
              <i data-lucide="${t.icon}" style="width:14px;height:14px;margin-right:4px"></i>
              ${t.label}
            </div>
          `).join('')}
        </div>

        <!-- Range Selector -->
        <div style="display:flex;gap:4px;margin-bottom:16px">
          ${ranges.map(r => `
            <button class="btn-${range === r ? 'primary' : 'secondary'} range-btn" data-range="${r}" style="padding:4px 12px;font-size:12px">${r}</button>
          `).join('')}
        </div>

        <!-- Content -->
        <div class="mc-card">
          <div class="mc-card-body">
            ${this._tabContent()}
          </div>
        </div>`;
    },

    _tabContent() {
        switch (this.state.tab) {
            case 'deploys': return this._deploysContent();
            case 'performance': return this._performanceContent();
            case 'logs': return this._logsContent();
            case 'analytics': return this._analyticsContent();
            default: return '';
        }
    },

    _deploysContent() {
        const deploys = this.state.deploys;
        if (!deploys || deploys.length === 0) {
            return '<div class="empty-state"><p class="empty-state-title">No deploys found</p><p class="empty-state-text">Deploy data will appear once sites are connected to Render.</p></div>';
        }

        return `<table class="mc-table">
          <thead><tr>
            <th>Status</th>
            <th>Date</th>
            <th>Commit</th>
            <th>Message</th>
            <th></th>
          </tr></thead>
          <tbody>
            ${deploys.map(d => {
                const status = d.status === 'live' ? 'success' : d.status === 'build_failed' ? 'danger' : 'info';
                const label = d.status === 'live' ? 'Live' : d.status === 'build_failed' ? 'Failed' : d.status || 'Unknown';
                const date = d.created_at ? new Date(d.created_at).toLocaleDateString('en-US', { month:'short', day:'numeric', hour:'numeric', minute:'2-digit' }) : 'N/A';
                return `<tr>
                  <td><span class="mc-badge mc-badge-${status}">${label}</span></td>
                  <td style="font-size:12px">${date}</td>
                  <td><code style="font-size:11px">${d.commit_sha || 'N/A'}</code></td>
                  <td style="font-size:12px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${this._esc(d.commit_message)}</td>
                  <td><button class="btn-ghost view-logs-btn" data-id="${d.id}" data-site="${d.site || ''}" style="font-size:11px">View Logs</button></td>
                </tr>`;
            }).join('')}
          </tbody>
        </table>`;
    },

    _performanceContent() {
        const data = this.state.performance;
        if (!data) return '<div class="empty-state"><p class="empty-state-text">Loading performance data...</p></div>';

        const sites = Array.isArray(data) ? data : [data];

        return sites.map(site => {
            const mobile = site.mobile || {};
            const desktop = site.desktop || {};

            const scoreColor = (s) => s >= 90 ? 'var(--green)' : s >= 50 ? 'var(--orange)' : 'var(--red)';
            const scoreBg = (s) => s >= 90 ? 'var(--green-bg)' : s >= 50 ? 'var(--orange-bg)' : 'var(--red-bg)';

            return `
            <div style="margin-bottom:24px">
              <h4 style="font-size:14px;font-weight:600;margin-bottom:12px">${site.name || site.site || 'Site'}</h4>
              <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px">
                <!-- Mobile Score -->
                <div class="stat-card" style="text-align:center">
                  <div class="score-badge" style="width:56px;height:56px;font-size:20px;margin:0 auto 8px;background:${scoreBg(mobile.score)};color:${scoreColor(mobile.score)}">${mobile.score || 0}</div>
                  <div class="stat-label">Mobile</div>
                </div>
                <!-- Desktop Score -->
                <div class="stat-card" style="text-align:center">
                  <div class="score-badge" style="width:56px;height:56px;font-size:20px;margin:0 auto 8px;background:${scoreBg(desktop.score)};color:${scoreColor(desktop.score)}">${desktop.score || 0}</div>
                  <div class="stat-label">Desktop</div>
                </div>
                <!-- Core Web Vitals -->
                <div class="stat-card">
                  <div style="font-size:12px;font-weight:600;margin-bottom:8px">Core Web Vitals</div>
                  <div style="display:grid;gap:4px;font-size:12px">
                    <div style="display:flex;justify-content:space-between"><span>FCP</span><span style="font-weight:600">${(mobile.fcp_ms/1000).toFixed(1)}s</span></div>
                    <div style="display:flex;justify-content:space-between"><span>LCP</span><span style="font-weight:600">${(mobile.lcp_ms/1000).toFixed(1)}s</span></div>
                    <div style="display:flex;justify-content:space-between"><span>CLS</span><span style="font-weight:600">${mobile.cls || 0}</span></div>
                    <div style="display:flex;justify-content:space-between"><span>TBT</span><span style="font-weight:600">${mobile.tbt_ms || 0}ms</span></div>
                  </div>
                </div>
              </div>
            </div>`;
        }).join('');
    },

    _logsContent() {
        const logs = this.state.logs;
        if (!logs || logs.length === 0) {
            return '<div class="empty-state"><p class="empty-state-text">No logs available</p></div>';
        }

        return `<div class="monitoring-log-viewer">
          ${logs.map(l => {
            const levelClass = l.level === 'ERROR' ? 'log-error' : l.level === 'WARN' ? 'log-warn' : 'log-info';
            const time = l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : '';
            return `<div class="log-entry ${levelClass}">
              <span class="log-time">${time}</span>
              <span class="log-level">${l.level}</span>
              <span class="log-message">${this._esc(l.message)}</span>
            </div>`;
          }).join('')}
        </div>`;
    },

    _analyticsContent() {
        const m = this.state.metrics;
        if (!m) return '<div class="empty-state"><p class="empty-state-text">Loading metrics...</p></div>';

        const statusCodes = m.status_codes || {};

        return `
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px">
          <div class="stat-card">
            <div class="stat-value">${(m.requests_total || 0).toLocaleString()}</div>
            <div class="stat-label">Total Requests</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">${m.bandwidth_mb || 0} MB</div>
            <div class="stat-label">Bandwidth</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">${m.avg_response_ms || 0}ms</div>
            <div class="stat-label">Avg Response</div>
          </div>
        </div>
        <div style="margin-top:16px">
          <h4 style="font-size:13px;font-weight:600;margin-bottom:8px">Status Codes</h4>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px">
            ${Object.entries(statusCodes).map(([code, count]) => `
              <div style="display:flex;align-items:center;gap:8px;font-size:13px">
                <span class="mc-badge ${code.startsWith('2') ? 'mc-badge-success' : code.startsWith('3') ? 'mc-badge-info' : 'mc-badge-danger'}">${code}</span>
                <span style="font-weight:600">${count.toLocaleString()}</span>
              </div>
            `).join('')}
          </div>
        </div>`;
    },

    _bindEvents(el) {
        // Tab switching
        el.querySelectorAll('.mc-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.state.tab = tab.dataset.tab;
                this.render(this.state.site);
            });
        });

        // Range switching
        el.querySelectorAll('.range-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.state.range = btn.dataset.range;
                this.render(this.state.site);
            });
        });

        // View logs buttons
        el.querySelectorAll('.view-logs-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const deployId = btn.dataset.id;
                const site = btn.dataset.site;
                try {
                    const detail = await API.get(`/monitoring/deploy/${deployId}`, { site });
                    alert(detail.logs || 'No logs available');
                } catch (e) {
                    alert('Failed to fetch logs');
                }
            });
        });
    },

    _esc(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    },
};

window.PageMonitoring = PageMonitoring;
