/**
 * Mission Control — Quality Loop Page
 * Displays quality loop runs with score progression charts,
 * iteration detail, and adversarial feedback.
 */
window.PageQuality = {
    container: null,
    _runs: [],
    _stats: null,
    _filterType: '',
    _filterStatus: '',
    _selectedRun: null,
    _chart: null,

    async render(company) {
        this.container = document.getElementById('page-quality');
        if (!this.container) return;

        this.container.innerHTML = this._renderLoading();

        try {
            const [stats, runs] = await Promise.all([
                API.quality.stats(company),
                API.quality.runs(company),
            ]);
            this._stats = stats;
            this._runs = runs;
            this._filterType = '';
            this._filterStatus = '';
            this._selectedRun = null;
            this._company = company;
            this._renderPage();
        } catch (err) {
            console.error('PageQuality load error:', err);
            this.container.innerHTML = this._renderError(err.message);
            if (window.lucide) lucide.createIcons();
        }
    },

    _renderLoading() {
        return `
            <div class="page-enter">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    ${Array(4).fill('<div class="skeleton skeleton-card" style="height:88px"></div>').join('')}
                </div>
                <div class="skeleton" style="height:56px;border-radius:8px;margin-bottom:24px"></div>
                <div class="skeleton" style="height:400px;border-radius:8px"></div>
            </div>
        `;
    },

    _renderError(message) {
        return `
            <div class="page-enter">
                <div class="mc-card">
                    <div class="empty-state">
                        <i data-lucide="alert-circle" class="empty-state-icon"></i>
                        <p class="empty-state-title">Failed to load quality data</p>
                        <p class="empty-state-text">${this._esc(message)}</p>
                    </div>
                </div>
            </div>
        `;
    },

    _renderPage() {
        const filtered = this._getFilteredRuns();
        const stats = this._stats || {};

        this.container.innerHTML = `
            <div class="page-enter">
                <!-- Stats Bar -->
                ${this._renderStatsBar(stats)}

                <!-- Content Type Breakdown -->
                ${this._renderTypeBreakdown(stats)}

                <!-- Filter Bar -->
                ${this._renderFilterBar(filtered.length)}

                <!-- Main Layout -->
                <div class="flex gap-6 mt-6">
                    <!-- Runs Table -->
                    <div class="flex-1">
                        ${filtered.length > 0 ? this._renderRunsTable(filtered) : `
                            <div class="mc-card">
                                <div class="empty-state">
                                    <i data-lucide="refresh-cw" class="empty-state-icon"></i>
                                    <p class="empty-state-title">No quality loop runs</p>
                                    <p class="empty-state-text">Run the quality loop CLI to generate content iterations.</p>
                                </div>
                            </div>
                        `}
                    </div>

                    <!-- Detail Panel -->
                    <div id="ql-detail-panel" class="${this._selectedRun ? '' : 'hidden'} w-full lg:max-w-[420px] flex-shrink-0">
                        ${this._selectedRun ? this._renderDetailPanel(this._selectedRun) : ''}
                    </div>
                </div>
            </div>
        `;

        if (window.lucide) lucide.createIcons();
        this._bindEvents();

        // Render chart if run is selected
        if (this._selectedRun && this._selectedRun.score_progression) {
            this._renderChart(this._selectedRun);
        }
    },

    // ── Stats Bar ──────────────────────────────────────────────

    _renderStatsBar(stats) {
        const total = stats.total_runs || 0;
        const avgScore = stats.avg_score || 0;
        const passRate = stats.pass_rate || 0;
        const avgIter = stats.avg_iterations || 0;

        const scoreColor = avgScore >= 9 ? 'text-[#00C875]' : avgScore >= 7 ? 'text-[#FDAB3D]' : 'text-[#E2445C]';
        const passColor = passRate >= 70 ? 'text-[#00C875]' : passRate >= 40 ? 'text-[#FDAB3D]' : 'text-[#E2445C]';

        return `
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value">${total}</div>
                            <div class="stat-label">Total Runs</div>
                        </div>
                        <div class="stat-icon bg-blue-50">
                            <i data-lucide="refresh-cw" class="w-5 h-5 text-[#0073EA]"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value ${scoreColor}">${avgScore.toFixed(1)}</div>
                            <div class="stat-label">Avg Score</div>
                        </div>
                        <div class="stat-icon bg-green-50">
                            <i data-lucide="target" class="w-5 h-5 text-[#00C875]"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value ${passColor}">${passRate}%</div>
                            <div class="stat-label">Pass Rate</div>
                        </div>
                        <div class="stat-icon bg-purple-50">
                            <i data-lucide="check-circle-2" class="w-5 h-5 text-[#A25DDC]"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value">${avgIter.toFixed(1)}</div>
                            <div class="stat-label">Avg Iterations</div>
                        </div>
                        <div class="stat-icon bg-orange-50">
                            <i data-lucide="repeat" class="w-5 h-5 text-[#FDAB3D]"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    // ── Content Type Breakdown ─────────────────────────────────

    _renderTypeBreakdown(stats) {
        const byType = stats.by_content_type || {};
        const types = Object.entries(byType);
        if (types.length === 0) return '';

        const typeIcons = {
            linkedin_post: 'linkedin',
            outreach_email: 'mail',
            aeo_capsule: 'brain',
            gbp_post: 'map-pin',
            review_response: 'star',
            blog_article: 'file-text',
        };
        const typeLabels = {
            linkedin_post: 'LinkedIn',
            outreach_email: 'Email',
            aeo_capsule: 'AEO',
            gbp_post: 'GBP',
            review_response: 'Reviews',
            blog_article: 'Blog',
        };

        return `
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
                ${types.map(([ct, data]) => {
                    const scoreColor = data.avg_score >= 9 ? '#00C875' : data.avg_score >= 7 ? '#FDAB3D' : '#E2445C';
                    return `
                        <div class="mc-card cursor-pointer hover:ring-2 hover:ring-[#0073EA]/20 transition-all"
                             data-filter-type="${ct}">
                            <div class="mc-card-body" style="padding:12px 16px">
                                <div class="flex items-center gap-2 mb-2">
                                    <i data-lucide="${typeIcons[ct] || 'file'}" class="w-4 h-4 text-[#676879]"></i>
                                    <span class="text-xs font-medium text-[#323338]">${typeLabels[ct] || ct}</span>
                                </div>
                                <div class="flex items-end justify-between">
                                    <div>
                                        <span class="text-lg font-bold" style="color:${scoreColor}">${data.avg_score.toFixed(1)}</span>
                                        <span class="text-xs text-[#676879]">/10</span>
                                    </div>
                                    <div class="text-right">
                                        <div class="text-xs text-[#676879]">${data.total} runs</div>
                                        <div class="text-xs font-medium" style="color:${scoreColor}">${data.pass_rate}% pass</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    },

    // ── Filter Bar ─────────────────────────────────────────────

    _renderFilterBar(count) {
        return `
            <div class="mc-card">
                <div class="mc-card-body" style="padding:12px 16px">
                    <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                        <div class="flex items-center gap-2">
                            <i data-lucide="filter" class="w-4 h-4 text-[#676879]"></i>
                            <select id="ql-type-filter"
                                class="border border-[#C5C7D0] rounded px-3 py-1.5 text-[13px] text-[#323338] focus:ring-2 focus:ring-[#0073EA]/20 focus:border-[#0073EA] outline-none bg-white">
                                <option value="">All Types</option>
                                <option value="linkedin_post" ${this._filterType === 'linkedin_post' ? 'selected' : ''}>LinkedIn Post</option>
                                <option value="outreach_email" ${this._filterType === 'outreach_email' ? 'selected' : ''}>Outreach Email</option>
                                <option value="aeo_capsule" ${this._filterType === 'aeo_capsule' ? 'selected' : ''}>AEO Capsule</option>
                                <option value="gbp_post" ${this._filterType === 'gbp_post' ? 'selected' : ''}>GBP Post</option>
                                <option value="review_response" ${this._filterType === 'review_response' ? 'selected' : ''}>Review Response</option>
                                <option value="blog_article" ${this._filterType === 'blog_article' ? 'selected' : ''}>Blog Article</option>
                            </select>
                        </div>
                        <div class="flex items-center gap-2">
                            <select id="ql-status-filter"
                                class="border border-[#C5C7D0] rounded px-3 py-1.5 text-[13px] text-[#323338] focus:ring-2 focus:ring-[#0073EA]/20 focus:border-[#0073EA] outline-none bg-white">
                                <option value="">All Statuses</option>
                                <option value="passed" ${this._filterStatus === 'passed' ? 'selected' : ''}>Passed</option>
                                <option value="max_iterations" ${this._filterStatus === 'max_iterations' ? 'selected' : ''}>Max Iterations</option>
                                <option value="failed" ${this._filterStatus === 'failed' ? 'selected' : ''}>Failed</option>
                            </select>
                        </div>
                        <div class="ml-auto text-xs text-[#676879]">${count} run${count !== 1 ? 's' : ''}</div>
                    </div>
                </div>
            </div>
        `;
    },

    // ── Runs Table ─────────────────────────────────────────────

    _renderRunsTable(runs) {
        const typeLabels = {
            linkedin_post: 'LinkedIn Post',
            outreach_email: 'Email',
            aeo_capsule: 'AEO Capsule',
            gbp_post: 'GBP Post',
            review_response: 'Review Response',
            blog_article: 'Blog Article',
        };

        return `
            <div class="mc-card">
                <div class="overflow-x-auto">
                    <table class="mc-table">
                        <thead>
                            <tr>
                                <th>Run ID</th>
                                <th>Type</th>
                                <th>Company</th>
                                <th>Score</th>
                                <th>Iterations</th>
                                <th>Status</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${runs.map(run => {
                                const score = run.final_score || 0;
                                const scoreColor = score >= 9 ? '#00C875' : score >= 7 ? '#FDAB3D' : '#E2445C';
                                const statusBadge = this._statusBadge(run.status);
                                const isSelected = this._selectedRun && this._selectedRun.id === run.id;
                                const date = run.created_at ? new Date(run.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '--';
                                const companyColor = this._companyColor(run.company_slug);

                                return `
                                    <tr class="cursor-pointer ${isSelected ? 'bg-[#F0F3FF]' : ''}"
                                        data-run-id="${run.id}">
                                        <td>
                                            <span class="text-xs font-mono text-[#676879]">${this._esc(run.id)}</span>
                                        </td>
                                        <td>
                                            <span class="text-[13px] text-[#323338]">${typeLabels[run.content_type] || run.content_type}</span>
                                        </td>
                                        <td>
                                            <div class="flex items-center gap-1.5">
                                                <span class="w-2 h-2 rounded-full flex-shrink-0" style="background:${companyColor}"></span>
                                                <span class="text-[13px] text-[#323338]">${this._esc(run.company || run.company_slug || '')}</span>
                                            </div>
                                        </td>
                                        <td>
                                            <span class="text-[13px] font-semibold" style="color:${scoreColor}">${score.toFixed(1)}</span>
                                            <span class="text-xs text-[#676879]">/10</span>
                                        </td>
                                        <td>
                                            <span class="text-[13px] text-[#323338]">${run.iteration_count || 0}</span>
                                        </td>
                                        <td>${statusBadge}</td>
                                        <td><span class="text-xs text-[#676879]">${date}</span></td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    // ── Detail Panel ───────────────────────────────────────────

    _renderDetailPanel(run) {
        const score = run.final_score || 0;
        const scoreColor = score >= 9 ? '#00C875' : score >= 7 ? '#FDAB3D' : '#E2445C';
        const iterations = run.iterations || [];

        return `
            <div class="space-y-4">
                <!-- Score Chart Card -->
                <div class="mc-card">
                    <div class="mc-card-header">
                        <h3 class="text-[13px] font-semibold text-[#323338]">Score Progression</h3>
                        <button id="ql-close-panel" class="btn-ghost text-xs">
                            <i data-lucide="x" class="w-4 h-4"></i>
                        </button>
                    </div>
                    <div class="mc-card-body">
                        <div class="flex items-center justify-between mb-3">
                            <div>
                                <span class="text-2xl font-bold" style="color:${scoreColor}">${score.toFixed(1)}</span>
                                <span class="text-sm text-[#676879]">/10 final</span>
                            </div>
                            ${this._statusBadge(run.status)}
                        </div>
                        <canvas id="ql-score-chart" height="160"></canvas>
                    </div>
                </div>

                <!-- Iterations -->
                ${iterations.map((it, idx) => this._renderIterationCard(it, idx, iterations.length)).join('')}
            </div>
        `;
    },

    _renderIterationCard(iteration, idx, total) {
        const score = iteration.overall_score || 0;
        const scoreColor = score >= 9 ? '#00C875' : score >= 7 ? '#FDAB3D' : '#E2445C';
        const passed = iteration.passed;
        const criteria = iteration.criteria_scores || [];
        const adversarial = iteration.adversarial_feedback || [];
        const isLast = idx === total - 1;

        return `
            <div class="mc-card ${isLast ? 'ring-1 ring-[#0073EA]/20' : ''}">
                <div class="mc-card-body">
                    <!-- Iteration Header -->
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                            <span class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold text-white"
                                  style="background:${scoreColor}">
                                ${iteration.iteration}
                            </span>
                            <span class="text-[13px] font-semibold text-[#323338]">Iteration ${iteration.iteration}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-sm font-bold" style="color:${scoreColor}">${score.toFixed(1)}</span>
                            ${passed ? '<i data-lucide="check-circle-2" class="w-4 h-4 text-[#00C875]"></i>' : '<i data-lucide="x-circle" class="w-4 h-4 text-[#E2445C]"></i>'}
                        </div>
                    </div>

                    <!-- Criteria Scores -->
                    ${criteria.length > 0 ? `
                        <div class="space-y-2 mb-3">
                            ${criteria.map(c => {
                                const cScore = c.score || 0;
                                const cColor = cScore >= 8 ? '#00C875' : cScore >= 6 ? '#FDAB3D' : '#E2445C';
                                const pct = Math.min(100, (cScore / 10) * 100);
                                return `
                                    <div>
                                        <div class="flex items-center justify-between mb-0.5">
                                            <span class="text-xs text-[#676879]">${this._esc(c.name)}</span>
                                            <span class="text-xs font-medium" style="color:${cColor}">${cScore.toFixed(1)}</span>
                                        </div>
                                        <div class="w-full bg-[#E6E9EF] rounded-full h-1">
                                            <div class="h-1 rounded-full transition-all duration-300" style="width:${pct}%;background:${cColor}"></div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : ''}

                    <!-- Adversarial Feedback -->
                    ${adversarial.length > 0 ? `
                        <div class="border-t border-[#E6E9EF] pt-2 mt-2">
                            <p class="text-[10px] uppercase tracking-wider text-[#676879] font-medium mb-2">Adversarial Feedback</p>
                            <div class="space-y-1.5">
                                ${adversarial.map(a => {
                                    const sevColor = a.severity === 'high' ? '#E2445C' : a.severity === 'medium' ? '#FDAB3D' : '#676879';
                                    return `
                                        <div class="flex items-start gap-2 text-xs">
                                            <span class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium text-white flex-shrink-0"
                                                  style="background:${sevColor}">${a.severity}</span>
                                            <div>
                                                <span class="font-medium text-[#323338]">${this._esc(a.persona)}:</span>
                                                <span class="text-[#676879]">${this._esc(a.critique || '').substring(0, 120)}</span>
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },

    // ── Chart ──────────────────────────────────────────────────

    _renderChart(run) {
        const canvas = document.getElementById('ql-score-chart');
        if (!canvas || !window.Chart) return;

        if (this._chart) {
            this._chart.destroy();
            this._chart = null;
        }

        const scores = run.score_progression || [];
        const labels = scores.map((_, i) => `Iter ${i + 1}`);
        const colors = scores.map(s => s >= 9 ? '#00C875' : s >= 7 ? '#FDAB3D' : '#E2445C');

        this._chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Score',
                    data: scores,
                    borderColor: '#0073EA',
                    backgroundColor: 'rgba(0, 115, 234, 0.08)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 6,
                    pointBackgroundColor: colors,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    borderWidth: 2,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#323338',
                        titleFont: { family: 'Inter', size: 12 },
                        bodyFont: { family: 'Inter', size: 12 },
                        callbacks: {
                            label: (ctx) => `Score: ${ctx.parsed.y.toFixed(1)}/10`,
                        },
                    },
                },
                scales: {
                    y: {
                        min: 0,
                        max: 10,
                        grid: { color: '#E6E9EF' },
                        ticks: {
                            font: { family: 'Inter', size: 11 },
                            color: '#676879',
                        },
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            font: { family: 'Inter', size: 11 },
                            color: '#676879',
                        },
                    },
                },
            },
        });
    },

    // ── Helpers ─────────────────────────────────────────────────

    _getFilteredRuns() {
        let result = this._runs || [];
        if (this._filterType) {
            result = result.filter(r => r.content_type === this._filterType);
        }
        if (this._filterStatus) {
            result = result.filter(r => r.status === this._filterStatus);
        }
        return result;
    },

    _bindEvents() {
        const container = this.container;

        // Type filter
        const typeFilter = container.querySelector('#ql-type-filter');
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this._filterType = e.target.value;
                this._renderPage();
            });
        }

        // Status filter
        const statusFilter = container.querySelector('#ql-status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this._filterStatus = e.target.value;
                this._renderPage();
            });
        }

        // Type breakdown cards as filters
        container.querySelectorAll('[data-filter-type]').forEach(card => {
            card.addEventListener('click', () => {
                const type = card.dataset.filterType;
                this._filterType = this._filterType === type ? '' : type;
                this._renderPage();
            });
        });

        // Run row click
        container.querySelectorAll('[data-run-id]').forEach(row => {
            row.addEventListener('click', () => {
                const id = row.dataset.runId;
                const run = this._runs.find(r => r.id === id);
                if (run) {
                    this._selectedRun = run;
                    this._renderPage();
                }
            });
        });

        // Close detail panel
        const closeBtn = container.querySelector('#ql-close-panel');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this._selectedRun = null;
                this._renderPage();
            });
        }
    },

    _statusBadge(status) {
        const map = {
            passed: { bg: '#00C875', label: 'Passed' },
            max_iterations: { bg: '#FDAB3D', label: 'Max Iter' },
            failed: { bg: '#E2445C', label: 'Failed' },
            running: { bg: '#0073EA', label: 'Running' },
        };
        const c = map[status] || { bg: '#676879', label: status || 'Unknown' };
        return `<span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium text-white" style="background:${c.bg}">${c.label}</span>`;
    },

    _companyColor(slug) {
        const colors = {
            'us-framing': '#579BFC',
            'us-drywall': '#FDAB3D',
            'us-exteriors': '#00C875',
            'us-development': '#C4C4C4',
        };
        return colors[slug] || '#676879';
    },

    _esc(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
};
