/**
 * Mission Control — Home / Dashboard Page
 * Premium redesign: breathing room, consistent cards, restrained color.
 */
window.PageHome = {
    _funnelChart: null,

    async render(company) {
        const container = document.getElementById('page-home');
        if (!container) return;

        container.innerHTML = `
            <div class="page-enter">
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}
                </div>
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    ${Array(3).fill('<div class="skeleton" style="height:240px;border-radius:12px"></div>').join('')}
                </div>
            </div>`;

        try {
            const [summary, funnel, gbp, postsList] = await Promise.all([
                API.dashboard.summary(company),
                API.reactivation.funnel(company),
                API.gbp.insights(),
                API.posts.list(company, 'scheduled').catch(() => ({ posts: [] })),
            ]);

            container.innerHTML = `<div class="page-enter">${this._buildHTML(summary, funnel, gbp, postsList)}</div>`;
            this._renderFunnelChart(funnel);
            if (window.lucide) lucide.createIcons();
        } catch (err) {
            console.error('PageHome.render error:', err);
            container.innerHTML = `
                <div class="mc-card">
                    <div class="empty-state">
                        <i data-lucide="alert-triangle" class="empty-state-icon"></i>
                        <p class="empty-state-title">Failed to load dashboard</p>
                        <p class="empty-state-text">${this._esc(err.message)}</p>
                    </div>
                </div>`;
            if (window.lucide) lucide.createIcons();
        }
    },

    _buildHTML(summary, funnel, gbp, postsList) {
        const li = summary.linkedin || {};
        const co = summary.content || {};
        const re = summary.reactivation || {};
        const tokens = summary.tokens || {};
        const gbpTotals = (gbp && gbp.totals) || {};
        const scheduledPosts = (postsList && postsList.posts) || [];

        return `
            ${this._statsBar(li, co, re)}
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
                ${this._postQueue(li, scheduledPosts)}
                ${this._contentPipeline(co)}
                ${this._leadFunnel(funnel)}
            </div>
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
                ${this._tokenHealth(tokens)}
                ${this._gbpInsights(gbpTotals)}
            </div>
        `;
    },

    _statsBar(li, co, re) {
        const stats = [
            { label: 'Scheduled Posts', value: this._num(li.scheduled), icon: 'send', color: 'bg-blue-50 text-blue-600' },
            { label: 'Published Articles', value: this._num(co.published), icon: 'file-check', color: 'bg-emerald-50 text-emerald-600' },
            { label: 'Active Leads', value: this._num(re.active_leads), icon: 'users', color: 'bg-amber-50 text-amber-600' },
            { label: 'Pipeline Value', value: this._currency(re.pipeline_value), icon: 'dollar-sign', color: 'bg-emerald-50/60 text-emerald-600' },
        ];
        return `
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-6">
                ${stats.map(s => `
                    <div class="stat-card-lg flex items-center gap-4">
                        <div class="stat-icon ${s.color}">
                            <i data-lucide="${s.icon}" class="w-5 h-5"></i>
                        </div>
                        <div class="min-w-0">
                            <div class="stat-value">${s.value}</div>
                            <div class="stat-label">${s.label}</div>
                        </div>
                    </div>
                `).join('')}
            </div>`;
    },

    _postQueue(li, scheduledPosts) {
        const posts = (scheduledPosts && scheduledPosts.length > 0) ? scheduledPosts : (li.scheduled_posts || []);
        const hasDetail = posts.length > 0;
        let listHTML;
        if (hasDetail) {
            listHTML = posts.slice(0, 5).map(p => `
                <div class="flex items-start gap-3 py-2.5 border-b border-gray-50 last:border-0">
                    <span class="company-dot company-dot-${this._esc(p.company_slug || p.company || 'us-framing')} mt-1.5 flex-shrink-0"></span>
                    <div class="min-w-0 flex-1">
                        <p class="text-sm text-[#323338] font-medium truncate">${this._esc(p.title || 'Untitled Post')}</p>
                        <p class="text-xs text-gray-400 mt-0.5">${this._fmtDate(p.scheduled_date || p.date || '')}</p>
                    </div>
                    <span class="badge badge-scheduled flex-shrink-0">Scheduled</span>
                </div>
            `).join('');
        } else {
            listHTML = `
                <div class="empty-state" style="padding:2rem 1rem;">
                    <i data-lucide="calendar" class="w-8 h-8 text-gray-300 mb-2"></i>
                    <p class="text-sm text-gray-500 font-medium">${this._num(li.scheduled)} posts in queue</p>
                </div>`;
        }
        return `
            <div class="mc-card">
                <div class="mc-card-header">
                    <h3 class="flex items-center gap-2">
                        <i data-lucide="linkedin" class="w-4 h-4 text-blue-500"></i>
                        Post Queue
                    </h3>
                    <a href="#calendar" class="btn-ghost text-xs">View All</a>
                </div>
                <div class="mc-card-body">
                    ${listHTML}
                    <div class="flex items-center justify-between text-xs text-gray-500 pt-3 mt-3 border-t border-gray-100">
                        <span>Published: <strong class="text-[#323338]">${this._num(li.published)}</strong></span>
                        <span>Drafts: <strong class="text-[#323338]">${this._num(li.drafts)}</strong></span>
                        <span>Engagement: <strong class="text-[#323338]">${this._num(li.total_engagement)}</strong></span>
                    </div>
                </div>
            </div>`;
    },

    _contentPipeline(co) {
        const stages = [
            { label: 'Draft', count: co.draft || co.drafts || 0, icon: 'file-edit', progressClass: 'progress-stage-draft' },
            { label: 'Review', count: co.review || co.in_review || 0, icon: 'eye', progressClass: 'progress-stage-review' },
            { label: 'Approved', count: co.approved || 0, icon: 'check-circle', progressClass: 'progress-stage-approved' },
            { label: 'Published', count: co.published || 0, icon: 'globe', progressClass: 'progress-stage-published' },
        ];
        const total = co.total_articles || stages.reduce((s, st) => s + st.count, 0);
        return `
            <div class="mc-card">
                <div class="mc-card-header">
                    <h3 class="flex items-center gap-2">
                        <i data-lucide="file-text" class="w-4 h-4 text-amber-600"></i>
                        Content Pipeline
                    </h3>
                    <a href="#content" class="btn-ghost text-xs">Manage</a>
                </div>
                <div class="mc-card-body">
                    <div class="space-y-4">
                        ${stages.map(st => {
                            const pct = total > 0 ? Math.round((st.count / total) * 100) : 0;
                            return `
                                <div>
                                    <div class="flex items-center justify-between mb-1.5">
                                        <span class="flex items-center gap-1.5 text-xs text-gray-600 font-medium">
                                            <i data-lucide="${st.icon}" class="w-3.5 h-3.5"></i>
                                            ${st.label}
                                        </span>
                                        <span class="text-xs font-semibold text-[#323338]">${st.count}</span>
                                    </div>
                                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                                        <div class="h-1.5 rounded-full transition-all duration-500 ${st.progressClass}"
                                             style="width: ${pct}%"></div>
                                    </div>
                                </div>`;
                        }).join('')}
                    </div>
                    <div class="mt-5 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                        <span>Total: <strong class="text-[#323338]">${this._num(total)}</strong></span>
                        ${co.avg_aeo_score != null ? `<span>Avg AEO: <strong class="text-[#323338]">${co.avg_aeo_score}</strong></span>` : ''}
                    </div>
                </div>
            </div>`;
    },

    _leadFunnel(funnel) {
        const counts = (funnel && funnel.counts) || {};
        const rates = (funnel && funnel.conversion_rates) || {};
        return `
            <div class="mc-card">
                <div class="mc-card-header">
                    <h3 class="flex items-center gap-2">
                        <i data-lucide="filter" class="w-4 h-4 text-emerald-600"></i>
                        Lead Funnel
                    </h3>
                    <a href="#reactivation" class="btn-ghost text-xs">Details</a>
                </div>
                <div class="mc-card-body">
                    <div class="funnel-chart-wrapper">
                        <canvas id="home-funnel-chart"></canvas>
                    </div>
                    <div class="mt-4 pt-3 border-t border-gray-100 grid grid-cols-2 gap-2 text-xs text-gray-500">
                        <span>Total: <strong class="text-[#323338]">${this._num(funnel.total)}</strong></span>
                        <span>Active: <strong class="text-[#323338]">${this._num(funnel.active)}</strong></span>
                        ${rates.overall != null ? `<span class="col-span-2">Conversion: <strong class="text-emerald-600">${rates.overall}%</strong></span>` : ''}
                    </div>
                </div>
            </div>`;
    },

    _tokenHealth(tokens) {
        const companies = [
            { slug: 'us-framing', name: 'US Framing' },
            { slug: 'us-drywall', name: 'US Drywall' },
            { slug: 'us-exteriors', name: 'US Exteriors' },
            { slug: 'us-development', name: 'US Development' },
        ];
        const statusLabel = (s) => {
            if (s === 'active') return { text: 'OK', cls: 'token-status-label-active' };
            if (s === 'expiring') return { text: 'Warning', cls: 'token-status-label-expiring' };
            return { text: 'Expired', cls: 'token-status-label-expired' };
        };
        const rows = companies.map(c => {
            const tokenData = tokens[c.slug] || {};
            const liStatus = tokenData.linkedin || tokenData.status || 'expired';
            const mondayStatus = tokenData.monday || 'active';
            const liLabel = statusLabel(liStatus);
            const monLabel = statusLabel(mondayStatus);
            return `
                <div class="flex items-center justify-between py-2.5 border-b border-gray-50 last:border-0">
                    <span class="flex items-center gap-2 text-sm font-medium text-gray-700">
                        <span class="company-dot company-dot-${c.slug}"></span>
                        ${c.name}
                    </span>
                    <div class="flex items-center gap-5">
                        <span class="token-health">
                            <span class="token-dot token-${this._esc(liStatus)}"></span>
                            <span class="text-xs text-gray-400">LI</span>
                            <span class="token-status-label ${liLabel.cls}">${liLabel.text}</span>
                        </span>
                        <span class="token-health">
                            <span class="token-dot token-${this._esc(mondayStatus)}"></span>
                            <span class="text-xs text-gray-400">Mon</span>
                            <span class="token-status-label ${monLabel.cls}">${monLabel.text}</span>
                        </span>
                    </div>
                </div>`;
        });
        return `
            <div class="mc-card">
                <div class="mc-card-header">
                    <h3 class="flex items-center gap-2">
                        <i data-lucide="shield-check" class="w-4 h-4 text-sky"></i>
                        Token Health
                    </h3>
                    <a href="#settings" class="btn-ghost text-xs">Manage</a>
                </div>
                <div class="mc-card-body">${rows.join('')}</div>
            </div>`;
    },

    _gbpInsights(totals) {
        const metrics = [
            { label: 'Views', value: this._num(totals.views), icon: 'eye', tint: 'gbp-metric-views', iconColor: 'text-blue-500' },
            { label: 'Clicks', value: this._num(totals.clicks), icon: 'mouse-pointer-click', tint: 'gbp-metric-clicks', iconColor: 'text-emerald-500' },
            { label: 'Calls', value: this._num(totals.calls), icon: 'phone', tint: 'gbp-metric-calls', iconColor: 'text-amber-500' },
            { label: 'Directions', value: this._num(totals.directions), icon: 'map-pin', tint: 'gbp-metric-directions', iconColor: 'text-violet-500' },
        ];
        return `
            <div class="mc-card">
                <div class="mc-card-header">
                    <h3 class="flex items-center gap-2">
                        <i data-lucide="map" class="w-4 h-4 text-forest"></i>
                        Google Business Profile
                    </h3>
                </div>
                <div class="mc-card-body">
                    <div class="grid grid-cols-2 gap-4">
                        ${metrics.map(m => `
                            <div class="gbp-metric-card ${m.tint} flex items-center gap-3">
                                <div class="w-10 h-10 rounded-xl bg-white/60 flex items-center justify-center flex-shrink-0">
                                    <i data-lucide="${m.icon}" class="w-5 h-5 ${m.iconColor}"></i>
                                </div>
                                <div>
                                    <div class="text-lg font-bold text-[#323338]">${m.value}</div>
                                    <div class="text-xs text-gray-500 font-medium">${m.label}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>`;
    },

    _renderFunnelChart(funnel) {
        if (this._funnelChart) { this._funnelChart.destroy(); this._funnelChart = null; }
        const canvas = document.getElementById('home-funnel-chart');
        if (!canvas) return;
        const counts = (funnel && funnel.counts) || {};
        const data = [counts.new || 0, counts.contacted || 0, counts.engaged || 0, counts.converted || 0];
        const ctx = canvas.getContext('2d');
        this._funnelChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['New', 'Contacted', 'Engaged', 'Converted'],
                datasets: [{ label: 'Leads', data: data, backgroundColor: ['#323338', '#579BFC', '#FDAB3D', '#00C875'], borderRadius: 4, barThickness: 20 }],
            },
            options: {
                indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { backgroundColor: '#323338', titleFont: { family: 'Inter', size: 12 }, bodyFont: { family: 'Inter', size: 11 }, cornerRadius: 6, padding: 10 } },
                scales: {
                    x: { beginAtZero: true, grid: { color: '#f3f4f6' }, ticks: { font: { family: 'Inter', size: 11 }, color: '#9ca3af', precision: 0 } },
                    y: { grid: { display: false }, ticks: { font: { family: 'Inter', size: 11, weight: '500' }, color: '#323338' } },
                },
            },
        });
    },

    _num(val) { if (val == null) return '0'; return Number(val).toLocaleString(); },
    _currency(val) { if (val == null) return '$0'; return '$' + Number(val).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 }); },
    _fmtDate(str) { if (!str) return ''; try { const d = new Date(str); if (isNaN(d.getTime())) return this._esc(str); return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); } catch { return this._esc(str); } },
    _esc(str) { if (str == null) return ''; const d = document.createElement('div'); d.textContent = String(str); return d.innerHTML; },
};
