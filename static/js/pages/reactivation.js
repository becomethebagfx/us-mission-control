/**
 * Mission Control — Reactivation Page Module
 * Premium redesign: skeleton loading, page-enter, breathing room, h-1.5 bars.
 */
window.PageReactivation = {
    _funnelChart: null,

    _currency(val) {
        if (val == null) return '$0';
        return '$' + Number(val).toLocaleString('en-US');
    },

    _formatDate(iso) {
        if (!iso) return '--';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '--';
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },

    _scoreBadgeClass(score) {
        if (score >= 80) return 'score-badge score-badge-green';
        if (score >= 60) return 'score-badge score-badge-blue';
        if (score >= 40) return 'score-badge score-badge-amber';
        return 'score-badge score-badge-red';
    },

    _companyDotClass(slug) {
        if (!slug) return '';
        return 'company-dot company-dot-' + slug;
    },

    async render(company) {
        const container = document.getElementById('page-reactivation');
        if (!container) return;

        container.innerHTML = `
            <div x-data="reactivationPage()" x-init="init('${company || ''}')" x-cloak>
                <!-- Tabs -->
                <div class="mc-tabs">
                    <button class="mc-tab" :class="currentTab === 'pipeline' ? 'mc-tab-active' : 'mc-tab-inactive'" @click="currentTab = 'pipeline'">
                        <span class="flex items-center gap-2"><i data-lucide="list" class="w-4 h-4"></i> Pipeline</span>
                    </button>
                    <button class="mc-tab" :class="currentTab === 'sequences' ? 'mc-tab-active' : 'mc-tab-inactive'" @click="currentTab = 'sequences'">
                        <span class="flex items-center gap-2"><i data-lucide="git-branch" class="w-4 h-4"></i> Sequences</span>
                    </button>
                    <button class="mc-tab" :class="currentTab === 'funnel' ? 'mc-tab-active' : 'mc-tab-inactive'" @click="switchToFunnel()">
                        <span class="flex items-center gap-2"><i data-lucide="bar-chart-3" class="w-4 h-4"></i> Funnel</span>
                    </button>
                </div>

                <!-- Loading -->
                <div x-show="loading" class="page-enter">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        ${Array(3).fill('<div class="skeleton skeleton-card" style="height:88px"></div>').join('')}
                    </div>
                    <div class="skeleton" style="height:320px;border-radius:12px"></div>
                </div>

                <!-- Tab: Pipeline -->
                <div x-show="!loading && currentTab === 'pipeline'" class="page-enter">
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="flex items-center gap-2">
                                <i data-lucide="users" class="w-4 h-4 text-[#323338]/60"></i>
                                Lead Pipeline
                            </h3>
                            <div class="flex items-center gap-3">
                                <span class="text-xs text-gray-500" x-text="leads.length + ' leads'"></span>
                                <span x-show="leads.length > pipelineLimit && !pipelineExpanded"
                                      class="text-xs text-gray-400" x-text="'Showing top ' + pipelineLimit"></span>
                            </div>
                        </div>
                        <div class="mc-card-body p-0">
                            <div class="overflow-x-auto">
                                <table class="mc-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Email</th>
                                            <th>Company</th>
                                            <th>Project Type</th>
                                            <th class="text-right">Deal Value</th>
                                            <th class="text-center">Score</th>
                                            <th class="text-center">Status</th>
                                            <th>Last Contact</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <template x-for="lead in visibleLeads" :key="lead.id">
                                            <tr>
                                                <td class="font-medium text-[#323338]" x-text="lead.name"></td>
                                                <td>
                                                    <a :href="'mailto:' + lead.email" class="text-blue-600 hover:underline text-xs" x-text="lead.email"></a>
                                                </td>
                                                <td>
                                                    <span class="flex items-center gap-1">
                                                        <span :class="companyDotClass(lead.company_slug)"></span>
                                                        <span class="text-xs" x-text="lead.company"></span>
                                                    </span>
                                                </td>
                                                <td class="text-xs text-gray-600" x-text="lead.project_type"></td>
                                                <td class="deal-value" x-text="formatCurrency(lead.deal_value)"></td>
                                                <td class="text-center">
                                                    <span :class="scoreBadgeClass(lead.score)" x-text="lead.score"></span>
                                                </td>
                                                <td class="text-center">
                                                    <span class="badge" :class="'badge-' + lead.status" x-text="lead.status"></span>
                                                </td>
                                                <td class="text-xs text-gray-500" x-text="formatDate(lead.last_contact)"></td>
                                            </tr>
                                        </template>
                                        <template x-if="leads.length === 0">
                                            <tr>
                                                <td colspan="8">
                                                    <div class="empty-state" style="padding:2rem 1rem">
                                                        <i data-lucide="users" class="empty-state-icon" style="width:2rem;height:2rem"></i>
                                                        <p class="empty-state-title">No leads found</p>
                                                        <p class="empty-state-text">Adjust filters or add new leads.</p>
                                                    </div>
                                                </td>
                                            </tr>
                                        </template>
                                    </tbody>
                                </table>
                            </div>
                            <!-- Show more / Show less toggle -->
                            <div x-show="leads.length > pipelineLimit">
                                <button class="pipeline-expand-btn" @click="pipelineExpanded = !pipelineExpanded">
                                    <template x-if="!pipelineExpanded">
                                        <span class="flex items-center gap-2">
                                            <i data-lucide="chevrons-down" class="w-4 h-4"></i>
                                            <span x-text="'Show all ' + leads.length + ' leads'"></span>
                                        </span>
                                    </template>
                                    <template x-if="pipelineExpanded">
                                        <span class="flex items-center gap-2">
                                            <i data-lucide="chevrons-up" class="w-4 h-4"></i>
                                            <span x-text="'Show top ' + pipelineLimit + ' only'"></span>
                                        </span>
                                    </template>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Tab: Sequences -->
                <div x-show="!loading && currentTab === 'sequences'" class="page-enter">
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="flex items-center gap-2">
                                <i data-lucide="git-branch" class="w-4 h-4 text-[#323338]/60"></i>
                                4-Touch Reactivation Sequence
                            </h3>
                            <span class="text-xs text-gray-500" x-text="sequenceTotal + ' total leads'"></span>
                        </div>
                        <div class="mc-card-body">
                            <!-- Sequence Timeline -->
                            <div class="relative">
                                <div class="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-gray-200 via-sky-200 to-green-200 mx-16" style="top: 1.75rem;"></div>

                                <div class="grid grid-cols-5 gap-4 relative">
                                    <!-- Step 0: Not Started -->
                                    <div class="flex flex-col items-center">
                                        <div class="seq-circle"
                                             :class="sequenceSteps['0'] > 0 ? 'bg-gray-400' : 'bg-gray-200'">
                                            <i data-lucide="inbox" class="w-5 h-5"></i>
                                        </div>
                                        <div class="mt-3 text-center">
                                            <p class="text-xs font-semibold text-gray-700">Not Started</p>
                                            <p class="text-xs text-gray-400 mt-0.5">Awaiting outreach</p>
                                            <p class="text-2xl font-bold text-[#323338] mt-1" x-text="sequenceSteps['0'] || 0"></p>
                                            <p class="text-xs text-gray-400">leads</p>
                                        </div>
                                    </div>

                                    <!-- Step 1: Touch 1 -->
                                    <div class="flex flex-col items-center">
                                        <div class="seq-circle"
                                             :class="sequenceSteps['1'] > 0 ? 'bg-sky' : 'bg-gray-200'">
                                            1
                                        </div>
                                        <div class="mt-3 text-center">
                                            <p class="text-xs font-semibold text-gray-700">Touch 1</p>
                                            <p class="text-xs text-gray-400 mt-0.5">Initial Outreach</p>
                                            <p class="text-2xl font-bold text-[#323338] mt-1" x-text="sequenceSteps['1'] || 0"></p>
                                            <p class="text-xs text-gray-400">leads</p>
                                        </div>
                                    </div>

                                    <!-- Step 2: Touch 2 -->
                                    <div class="flex flex-col items-center">
                                        <div class="seq-circle"
                                             :class="sequenceSteps['2'] > 0 ? 'bg-indigo-500' : 'bg-gray-200'">
                                            2
                                        </div>
                                        <div class="mt-3 text-center">
                                            <p class="text-xs font-semibold text-gray-700">Touch 2</p>
                                            <p class="text-xs text-gray-400 mt-0.5">Value Follow-Up</p>
                                            <p class="text-2xl font-bold text-[#323338] mt-1" x-text="sequenceSteps['2'] || 0"></p>
                                            <p class="text-xs text-gray-400">leads</p>
                                        </div>
                                    </div>

                                    <!-- Step 3: Touch 3 -->
                                    <div class="flex flex-col items-center">
                                        <div class="seq-circle"
                                             :class="sequenceSteps['3'] > 0 ? 'bg-purple-500' : 'bg-gray-200'">
                                            3
                                        </div>
                                        <div class="mt-3 text-center">
                                            <p class="text-xs font-semibold text-gray-700">Touch 3</p>
                                            <p class="text-xs text-gray-400 mt-0.5">Case Study Send</p>
                                            <p class="text-2xl font-bold text-[#323338] mt-1" x-text="sequenceSteps['3'] || 0"></p>
                                            <p class="text-xs text-gray-400">leads</p>
                                        </div>
                                    </div>

                                    <!-- Step 4: Touch 4 -->
                                    <div class="flex flex-col items-center">
                                        <div class="seq-circle"
                                             :class="sequenceSteps['4'] > 0 ? 'bg-green-500' : 'bg-gray-200'">
                                            4
                                        </div>
                                        <div class="mt-3 text-center">
                                            <p class="text-xs font-semibold text-gray-700">Touch 4</p>
                                            <p class="text-xs text-gray-400 mt-0.5">Final Offer</p>
                                            <p class="text-2xl font-bold text-[#323338] mt-1" x-text="sequenceSteps['4'] || 0"></p>
                                            <p class="text-xs text-gray-400">leads</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Sequence Summary Cards -->
                            <div class="grid grid-cols-3 gap-4 mt-8 pt-6 border-t border-gray-100">
                                <div class="stat-card text-center">
                                    <div class="stat-value" x-text="sequenceSteps['0'] || 0"></div>
                                    <div class="stat-label">Not Yet Contacted</div>
                                </div>
                                <div class="stat-card text-center">
                                    <div class="stat-value" x-text="(sequenceSteps['1'] || 0) + (sequenceSteps['2'] || 0) + (sequenceSteps['3'] || 0)"></div>
                                    <div class="stat-label">In Sequence</div>
                                </div>
                                <div class="stat-card text-center">
                                    <div class="stat-value" x-text="sequenceSteps['4'] || 0"></div>
                                    <div class="stat-label">Sequence Complete</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Tab: Funnel -->
                <div x-show="!loading && currentTab === 'funnel'" class="page-enter">
                    <!-- Funnel Stats Row -->
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                        <div class="stat-card">
                            <div class="flex items-center justify-between">
                                <div>
                                    <div class="stat-value" x-text="funnelData.total || 0"></div>
                                    <div class="stat-label">Total Leads</div>
                                </div>
                                <div class="stat-icon bg-blue-50">
                                    <i data-lucide="users" class="w-5 h-5 text-blue-600"></i>
                                </div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="flex items-center justify-between">
                                <div>
                                    <div class="stat-value" x-text="(funnelData.conversion_rates?.converted_rate || 0) + '%'"></div>
                                    <div class="stat-label">Conversion Rate</div>
                                </div>
                                <div class="stat-icon bg-green-50">
                                    <i data-lucide="trending-up" class="w-5 h-5 text-green-600"></i>
                                </div>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="flex items-center justify-between">
                                <div>
                                    <div class="stat-value" x-text="formatCurrency(pipelineValue)"></div>
                                    <div class="stat-label">Pipeline Value</div>
                                </div>
                                <div class="stat-icon bg-gold/10">
                                    <i data-lucide="dollar-sign" class="w-5 h-5 text-gold"></i>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Funnel Chart -->
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="flex items-center gap-2">
                                <i data-lucide="bar-chart-3" class="w-4 h-4 text-[#323338]/60"></i>
                                Reactivation Funnel
                            </h3>
                        </div>
                        <div class="mc-card-body">
                            <div style="height: 320px; position: relative;">
                                <canvas id="funnel-chart"></canvas>
                            </div>
                        </div>
                    </div>

                    <!-- Funnel Breakdown -->
                    <div class="mc-card mt-6">
                        <div class="mc-card-header">
                            <h3>Stage Breakdown</h3>
                        </div>
                        <div class="mc-card-body">
                            <div class="space-y-4">
                                <!-- New -->
                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="flex items-center gap-2">
                                            <span class="badge badge-new">new</span>
                                            <span class="text-sm text-gray-600">Leads entered pipeline</span>
                                        </span>
                                        <span class="text-sm font-semibold" x-text="funnelData.counts?.new || 0"></span>
                                    </div>
                                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                                        <div class="funnel-bar h-1.5 rounded-l-lg bg-blue-400" :style="'width:' + funnelBarWidth('new') + '%'"></div>
                                    </div>
                                </div>
                                <!-- Contacted -->
                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="flex items-center gap-2">
                                            <span class="badge badge-contacted">contacted</span>
                                            <span class="text-sm text-gray-600" x-text="(funnelData.conversion_rates?.contacted_rate || 0) + '% of total'"></span>
                                        </span>
                                        <span class="text-sm font-semibold" x-text="funnelData.counts?.contacted || 0"></span>
                                    </div>
                                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                                        <div class="funnel-bar h-1.5 rounded-l-lg bg-purple-400" :style="'width:' + funnelBarWidth('contacted') + '%'"></div>
                                    </div>
                                </div>
                                <!-- Engaged -->
                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="flex items-center gap-2">
                                            <span class="badge badge-engaged">engaged</span>
                                            <span class="text-sm text-gray-600" x-text="(funnelData.conversion_rates?.engaged_rate || 0) + '% of total'"></span>
                                        </span>
                                        <span class="text-sm font-semibold" x-text="funnelData.counts?.engaged || 0"></span>
                                    </div>
                                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                                        <div class="funnel-bar h-1.5 rounded-l-lg bg-indigo-400" :style="'width:' + funnelBarWidth('engaged') + '%'"></div>
                                    </div>
                                </div>
                                <!-- Converted -->
                                <div>
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="flex items-center gap-2">
                                            <span class="badge badge-converted">converted</span>
                                            <span class="text-sm text-gray-600" x-text="(funnelData.conversion_rates?.converted_rate || 0) + '% of total'"></span>
                                        </span>
                                        <span class="text-sm font-semibold" x-text="funnelData.counts?.converted || 0"></span>
                                    </div>
                                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                                        <div class="funnel-bar h-1.5 rounded-l-lg bg-green-500" :style="'width:' + funnelBarWidth('converted') + '%'"></div>
                                    </div>
                                </div>
                                <!-- Dead -->
                                <div class="pt-2 border-t border-gray-100">
                                    <div class="flex items-center justify-between mb-1">
                                        <span class="flex items-center gap-2">
                                            <span class="badge badge-dead">dead</span>
                                            <span class="text-sm text-gray-600" x-text="(funnelData.conversion_rates?.dead_rate || 0) + '% of total'"></span>
                                        </span>
                                        <span class="text-sm font-semibold" x-text="funnelData.counts?.dead || 0"></span>
                                    </div>
                                    <div class="w-full bg-gray-100 rounded-full h-1.5">
                                        <div class="funnel-bar h-1.5 rounded-l-lg bg-gray-300" :style="'width:' + funnelBarWidth('dead') + '%'"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Register Alpine component
        if (!Alpine._reactivationRegistered) {
            Alpine.data('reactivationPage', () => ({
                currentTab: 'pipeline',
                loading: true,
                leads: [],
                funnelData: {},
                metricsData: {},
                sequenceSteps: {},
                sequenceTotal: 0,
                pipelineValue: 0,
                pipelineLimit: 15,
                pipelineExpanded: false,
                _company: '',

                async init(company) {
                    this._company = company;
                    this.loading = true;
                    try {
                        await this.loadData();
                    } catch (err) {
                        console.error('Reactivation page load error:', err);
                    } finally {
                        this.loading = false;
                        this.$nextTick(() => {
                            if (window.lucide) lucide.createIcons();
                        });
                    }
                },

                async loadData() {
                    const company = this._company || null;

                    const [leadsRes, funnelRes, metricsRes, seqRes] = await Promise.all([
                        API.reactivation.leads(company),
                        API.reactivation.funnel(company),
                        API.reactivation.metrics(company),
                        API.reactivation.sequences(),
                    ]);

                    this.leads = leadsRes.leads || [];
                    this.funnelData = funnelRes || {};
                    this.metricsData = metricsRes || {};
                    this.pipelineValue = metricsRes.total_pipeline_value || 0;

                    const seqs = seqRes.sequences || {};
                    this.sequenceTotal = seqRes.total || 0;
                    this.sequenceSteps = {};
                    for (const step of ['0', '1', '2', '3', '4']) {
                        this.sequenceSteps[step] = seqs[step]?.count || 0;
                    }
                },

                get sortedLeads() {
                    return [...this.leads].sort((a, b) => (b.score || 0) - (a.score || 0));
                },

                get visibleLeads() {
                    const sorted = this.sortedLeads;
                    if (this.pipelineExpanded || sorted.length <= this.pipelineLimit) {
                        return sorted;
                    }
                    return sorted.slice(0, this.pipelineLimit);
                },

                formatCurrency(val) {
                    if (val == null) return '$0';
                    return '$' + Number(val).toLocaleString('en-US');
                },

                formatDate(iso) {
                    if (!iso) return '--';
                    const d = new Date(iso);
                    if (isNaN(d.getTime())) return '--';
                    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                },

                scoreBadgeClass(score) {
                    if (score >= 80) return 'score-badge score-badge-green';
                    if (score >= 60) return 'score-badge score-badge-blue';
                    if (score >= 40) return 'score-badge score-badge-amber';
                    return 'score-badge score-badge-red';
                },

                companyDotClass(slug) {
                    if (!slug) return '';
                    return 'company-dot company-dot-' + slug;
                },

                funnelBarWidth(status) {
                    const counts = this.funnelData.counts || {};
                    const total = this.funnelData.total || 1;
                    const count = counts[status] || 0;
                    return Math.max(2, Math.round((count / total) * 100));
                },

                switchToFunnel() {
                    this.currentTab = 'funnel';
                    this.$nextTick(() => {
                        this.renderFunnelChart();
                        if (window.lucide) lucide.createIcons();
                    });
                },

                renderFunnelChart() {
                    const canvas = document.getElementById('funnel-chart');
                    if (!canvas) return;

                    if (window.PageReactivation._funnelChart) {
                        window.PageReactivation._funnelChart.destroy();
                        window.PageReactivation._funnelChart = null;
                    }

                    const counts = this.funnelData.counts || {};
                    const stages = ['new', 'contacted', 'engaged', 'converted'];
                    const deadCount = counts.dead || 0;
                    const stageLabels = ['New', 'Contacted', 'Engaged', 'Converted', 'Dead'];
                    const stageValues = stages.map(s => counts[s] || 0).concat([deadCount]);
                    const stageColors = [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(147, 51, 234, 0.8)',
                        'rgba(99, 102, 241, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(156, 163, 175, 0.6)',
                    ];
                    const stageBorders = [
                        'rgba(59, 130, 246, 1)',
                        'rgba(147, 51, 234, 1)',
                        'rgba(99, 102, 241, 1)',
                        'rgba(34, 197, 94, 1)',
                        'rgba(156, 163, 175, 1)',
                    ];

                    const ctx = canvas.getContext('2d');
                    window.PageReactivation._funnelChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: stageLabels,
                            datasets: [{
                                label: 'Leads',
                                data: stageValues,
                                backgroundColor: stageColors,
                                borderColor: stageBorders,
                                borderWidth: 1,
                                borderRadius: 6,
                            }],
                        },
                        options: {
                            indexAxis: 'y',
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: '#1B2A4A',
                                    titleFont: { family: 'Inter', size: 12 },
                                    bodyFont: { family: 'Inter', size: 11 },
                                    cornerRadius: 6,
                                    padding: 10,
                                    callbacks: {
                                        label: function(ctx) {
                                            return ctx.parsed.x + ' leads';
                                        },
                                    },
                                },
                            },
                            scales: {
                                x: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1,
                                        font: { family: 'Inter', size: 11 },
                                        color: '#9ca3af',
                                    },
                                    grid: { color: 'rgba(0,0,0,0.05)' },
                                },
                                y: {
                                    ticks: {
                                        font: { family: 'Inter', size: 12, weight: '500' },
                                        color: '#1B2A4A',
                                    },
                                    grid: { display: false },
                                },
                            },
                        },
                    });
                },
            }));
            Alpine._reactivationRegistered = true;
        }

        // Initialize Alpine on the new content
        Alpine.initTree(container);
    },
};
