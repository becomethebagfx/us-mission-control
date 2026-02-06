/**
 * Mission Control — Settings Page Module
 * Premium redesign: skeleton loading, breathing room, consistent cards.
 */
window.PageSettings = {

    _formatDate(iso) {
        if (!iso) return '--';
        const d = new Date(iso);
        if (isNaN(d.getTime())) return '--';
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },

    async render() {
        const container = document.getElementById('page-settings');
        if (!container) return;

        container.innerHTML = `
            <div x-data="settingsPage()" x-init="init()" x-cloak>
                <!-- Loading -->
                <div x-show="loading" class="page-enter">
                    <div class="space-y-8">
                        <div class="skeleton" style="height:200px;border-radius:12px"></div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            ${Array(4).fill('<div class="skeleton" style="height:240px;border-radius:12px"></div>').join('')}
                        </div>
                        <div class="skeleton" style="height:160px;border-radius:12px"></div>
                    </div>
                </div>

                <div x-show="!loading" class="space-y-8 page-enter">

                    <!-- Section 1: OAuth Token Status -->
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="flex items-center gap-2">
                                <i data-lucide="shield-check" class="w-4 h-4 text-navy/60"></i>
                                OAuth Token Status
                            </h3>
                            <span class="text-xs text-gray-500" x-text="tokenList.length + ' companies'"></span>
                        </div>
                        <div class="mc-card-body p-0">
                            <div class="overflow-x-auto">
                                <table class="mc-table mc-table-divided">
                                    <thead>
                                        <tr>
                                            <th>Company</th>
                                            <th>LinkedIn Token</th>
                                            <th>Expires</th>
                                            <th>Last Refreshed</th>
                                            <th>Monday.com</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <template x-for="token in tokenList" :key="token.company_slug || token.company">
                                            <tr>
                                                <td>
                                                    <span class="flex items-center gap-2">
                                                        <span :class="companyDotClass(token.company_slug)"></span>
                                                        <span class="font-medium text-navy" x-text="token.company"></span>
                                                    </span>
                                                </td>
                                                <td>
                                                    <span class="token-health">
                                                        <span class="token-dot" :class="tokenDotClass(token.linkedin_token?.status)"></span>
                                                        <span class="capitalize" :class="tokenTextClass(token.linkedin_token?.status)" x-text="token.linkedin_token?.status || 'unknown'"></span>
                                                    </span>
                                                </td>
                                                <td class="text-xs text-gray-500" x-text="formatDate(token.linkedin_token?.expires_at)"></td>
                                                <td class="text-xs text-gray-500" x-text="formatDate(token.linkedin_token?.last_refreshed)"></td>
                                                <td>
                                                    <span class="token-health">
                                                        <span class="token-dot" :class="mondayDotClass(token.monday_token)"></span>
                                                        <span class="capitalize" :class="mondayTextClass(token.monday_token)" x-text="mondayStatusLabel(token.monday_token)"></span>
                                                    </span>
                                                </td>
                                            </tr>
                                        </template>
                                        <template x-if="tokenList.length === 0">
                                            <tr>
                                                <td colspan="5">
                                                    <div class="empty-state" style="padding:2rem 1rem">
                                                        <i data-lucide="shield-off" class="empty-state-icon" style="width:2rem;height:2rem"></i>
                                                        <p class="empty-state-title">No token data available</p>
                                                    </div>
                                                </td>
                                            </tr>
                                        </template>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <!-- Section 2: Company Configurations -->
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="flex items-center gap-2">
                                <i data-lucide="building-2" class="w-4 h-4 text-navy/60"></i>
                                Company Configurations
                            </h3>
                            <span class="text-xs text-gray-500" x-text="companies.length + ' companies (' + activeCompanyCount + ' active)'"></span>
                        </div>
                        <div class="mc-card-body">
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <template x-for="co in companies" :key="co.slug">
                                    <div class="company-config-card"
                                         :style="'border-left-color:' + (co.accent_color || '#ccc')">
                                        <!-- Company Header -->
                                        <div class="flex items-center gap-3 mb-4">
                                            <div class="w-5 h-5 rounded-full flex-shrink-0" :style="'background:' + (co.accent_color || '#ccc')"></div>
                                            <div class="min-w-0">
                                                <h4 class="font-semibold text-navy" x-text="co.name"></h4>
                                                <span class="text-[10px] text-gray-400 font-mono" x-text="co.slug"></span>
                                            </div>
                                            <span x-show="!co.active" class="badge badge-draft ml-auto flex-shrink-0">Coming Soon</span>
                                        </div>

                                        <!-- Company Details -->
                                        <div class="space-y-2 text-sm">
                                            <div x-show="co.tagline" class="text-gray-600 italic text-xs mb-3" x-text="co.tagline"></div>

                                            <div class="flex items-start gap-2" x-show="co.website">
                                                <i data-lucide="globe" class="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0"></i>
                                                <a :href="co.website" target="_blank" class="text-blue-600 hover:underline text-xs truncate" x-text="co.website"></a>
                                            </div>

                                            <div class="flex items-start gap-2" x-show="co.phone">
                                                <i data-lucide="phone" class="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0"></i>
                                                <span class="text-xs text-gray-600" x-text="co.phone"></span>
                                            </div>

                                            <div class="flex items-start gap-2" x-show="co.email">
                                                <i data-lucide="mail" class="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0"></i>
                                                <a :href="'mailto:' + co.email" class="text-blue-600 hover:underline text-xs" x-text="co.email"></a>
                                            </div>

                                            <div class="flex items-start gap-2" x-show="co.address">
                                                <i data-lucide="map-pin" class="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0"></i>
                                                <span class="text-xs text-gray-600" x-text="co.address"></span>
                                            </div>

                                            <div x-show="co.services && co.services.length > 0" class="mt-3 pt-3 border-t border-gray-100">
                                                <p class="text-[10px] font-medium text-gray-500 uppercase tracking-wide mb-2">Services</p>
                                                <div class="flex flex-wrap gap-1.5">
                                                    <template x-for="svc in (co.services || [])" :key="svc">
                                                        <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600" x-text="svc"></span>
                                                    </template>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </template>
                            </div>
                        </div>
                    </div>

                    <!-- Section 3: System Info -->
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="flex items-center gap-2">
                                <i data-lucide="server" class="w-4 h-4 text-navy/60"></i>
                                System Information
                            </h3>
                        </div>
                        <div class="mc-card-body">
                            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <!-- App Name -->
                                <div class="sys-info-tile" style="background: linear-gradient(135deg, rgba(27,42,74,0.04) 0%, rgba(27,42,74,0.08) 100%);">
                                    <div class="sys-icon bg-navy/10">
                                        <i data-lucide="layout-dashboard" class="w-5 h-5 text-navy"></i>
                                    </div>
                                    <div>
                                        <p class="text-[10px] text-gray-500 font-medium uppercase tracking-wide">App Name</p>
                                        <p class="text-sm font-semibold text-navy" x-text="systemInfo.app_name || '--'"></p>
                                    </div>
                                </div>

                                <!-- Version -->
                                <div class="sys-info-tile" style="background: linear-gradient(135deg, rgba(14,165,233,0.04) 0%, rgba(14,165,233,0.08) 100%);">
                                    <div class="sys-icon bg-blue-50">
                                        <i data-lucide="tag" class="w-5 h-5 text-blue-600"></i>
                                    </div>
                                    <div>
                                        <p class="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Version</p>
                                        <p class="text-sm font-semibold text-navy" x-text="'v' + (systemInfo.version || '0.0.0')"></p>
                                    </div>
                                </div>

                                <!-- Demo Mode -->
                                <div class="sys-info-tile"
                                     :style="systemInfo.demo_mode
                                         ? 'background: linear-gradient(135deg, rgba(245,158,11,0.04) 0%, rgba(245,158,11,0.08) 100%)'
                                         : 'background: linear-gradient(135deg, rgba(34,197,94,0.04) 0%, rgba(34,197,94,0.08) 100%)'">
                                    <div class="sys-icon"
                                         :class="systemInfo.demo_mode ? 'bg-amber-50' : 'bg-green-50'">
                                        <i data-lucide="flask-conical" class="w-5 h-5"
                                           :class="systemInfo.demo_mode ? 'text-amber-600' : 'text-green-600'"></i>
                                    </div>
                                    <div>
                                        <p class="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Demo Mode</p>
                                        <p class="text-sm font-semibold" :class="systemInfo.demo_mode ? 'text-amber-600' : 'text-green-600'" x-text="systemInfo.demo_mode ? 'Enabled' : 'Disabled'"></p>
                                    </div>
                                </div>

                                <!-- Host -->
                                <div class="sys-info-tile" style="background: linear-gradient(135deg, rgba(107,114,128,0.04) 0%, rgba(107,114,128,0.08) 100%);">
                                    <div class="sys-icon bg-gray-100">
                                        <i data-lucide="monitor" class="w-5 h-5 text-gray-600"></i>
                                    </div>
                                    <div>
                                        <p class="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Host</p>
                                        <p class="text-sm font-mono font-semibold text-navy" x-text="(systemInfo.host || '--') + ':' + (systemInfo.port || '--')"></p>
                                    </div>
                                </div>

                                <!-- Data Directory -->
                                <div class="sys-info-tile" style="background: linear-gradient(135deg, rgba(107,114,128,0.04) 0%, rgba(107,114,128,0.08) 100%);">
                                    <div class="sys-icon bg-gray-100">
                                        <i data-lucide="folder" class="w-5 h-5 text-gray-600"></i>
                                    </div>
                                    <div class="min-w-0">
                                        <p class="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Data Directory</p>
                                        <p class="text-sm font-mono font-semibold text-navy truncate" x-text="systemInfo.data_dir || '--'" style="max-width: 200px;"></p>
                                    </div>
                                </div>

                                <!-- Active Companies -->
                                <div class="sys-info-tile" style="background: linear-gradient(135deg, rgba(34,197,94,0.04) 0%, rgba(34,197,94,0.08) 100%);">
                                    <div class="sys-icon bg-green-50">
                                        <i data-lucide="building-2" class="w-5 h-5 text-green-600"></i>
                                    </div>
                                    <div>
                                        <p class="text-[10px] text-gray-500 font-medium uppercase tracking-wide">Active Companies</p>
                                        <p class="text-sm font-semibold text-navy" x-text="(systemInfo.active_companies_count || 0) + ' / ' + (systemInfo.companies_count || 0)"></p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        `;

        // Register Alpine component
        if (!Alpine._settingsRegistered) {
            Alpine.data('settingsPage', () => ({
                loading: true,
                tokenList: [],
                companies: [],
                activeCompanyCount: 0,
                systemInfo: {},

                async init() {
                    this.loading = true;
                    try {
                        await this.loadData();
                    } catch (err) {
                        console.error('Settings page load error:', err);
                    } finally {
                        this.loading = false;
                        this.$nextTick(() => {
                            if (window.lucide) lucide.createIcons();
                        });
                    }
                },

                async loadData() {
                    const [tokensRes, companiesRes, systemRes] = await Promise.all([
                        API.settings.tokens(),
                        API.settings.companies(),
                        API.settings.system(),
                    ]);

                    const tokensRaw = tokensRes.tokens || {};
                    if (Array.isArray(tokensRaw)) {
                        this.tokenList = tokensRaw;
                    } else {
                        this.tokenList = Object.entries(tokensRaw).map(([key, val]) => ({
                            company: val.company || key,
                            company_slug: val.company_slug || key,
                            linkedin_token: val.linkedin_token || {},
                            monday_token: val.monday_token || {},
                        }));
                    }

                    this.companies = companiesRes.companies || [];
                    this.activeCompanyCount = companiesRes.active || 0;

                    this.systemInfo = systemRes || {};
                },

                formatDate(iso) {
                    if (!iso) return '--';
                    const d = new Date(iso);
                    if (isNaN(d.getTime())) return '--';
                    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                },

                companyDotClass(slug) {
                    if (!slug) return '';
                    return 'company-dot company-dot-' + slug;
                },

                tokenDotClass(status) {
                    if (status === 'active') return 'token-active';
                    if (status === 'expiring') return 'token-expiring';
                    if (status === 'expired') return 'token-expired';
                    return 'bg-gray-300';
                },

                tokenTextClass(status) {
                    if (status === 'active') return 'text-green-600';
                    if (status === 'expiring') return 'text-amber-600';
                    if (status === 'expired') return 'text-red-600';
                    return 'text-gray-400';
                },

                mondayDotClass(token) {
                    if (!token) return 'bg-gray-300';
                    const status = token.status || '';
                    if (status === 'active' && token.connected) return 'token-active';
                    if (status === 'disconnected') return 'token-expired';
                    return 'bg-gray-300';
                },

                mondayTextClass(token) {
                    if (!token) return 'text-gray-400';
                    const status = token.status || '';
                    if (status === 'active' && token.connected) return 'text-green-600';
                    if (status === 'disconnected') return 'text-red-600';
                    return 'text-gray-400';
                },

                mondayStatusLabel(token) {
                    if (!token) return 'Unknown';
                    const status = token.status || 'unknown';
                    if (status === 'active' && token.connected) return 'Connected';
                    if (status === 'disconnected') return 'Disconnected';
                    return status;
                },
            }));
            Alpine._settingsRegistered = true;
        }

        // Initialize Alpine on the new content
        Alpine.initTree(container);
    },
};
