/**
 * Mission Control — Google Business Profile Page
 * Premium redesign: stat-card pattern, breathing room, icon-paired metrics.
 */
window.PageGBP = {
    async render(company) {
        const container = document.getElementById('page-gbp');
        if (!container) return;

        container.innerHTML = `
            <div class="page-enter">
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}
                </div>
                <div class="skeleton" style="height:320px;border-radius:12px"></div>
            </div>`;

        try {
            const [locations, insights] = await Promise.all([
                API.gbp.locations(),
                API.gbp.insights(),
            ]);

            const locs = locations.locations || locations || [];
            const ins = insights.insights || insights || {};
            const totals = ins.totals || ins || {};

            container.innerHTML = `<div class="page-enter">
                <!-- Stats -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${this._fmt(totals.views || 0)}</div>
                                <div class="stat-label">Total Views</div>
                            </div>
                            <div class="stat-icon bg-blue-50">
                                <i data-lucide="eye" class="w-5 h-5 text-blue-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${this._fmt(totals.clicks || 0)}</div>
                                <div class="stat-label">Clicks</div>
                            </div>
                            <div class="stat-icon bg-emerald-50">
                                <i data-lucide="mouse-pointer-click" class="w-5 h-5 text-emerald-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${this._fmt(totals.calls || 0)}</div>
                                <div class="stat-label">Calls</div>
                            </div>
                            <div class="stat-icon bg-amber-50">
                                <i data-lucide="phone" class="w-5 h-5 text-amber-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${this._fmt(totals.directions || 0)}</div>
                                <div class="stat-label">Directions</div>
                            </div>
                            <div class="stat-icon bg-violet-50">
                                <i data-lucide="map-pin" class="w-5 h-5 text-violet-600"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Locations -->
                <div class="mc-card">
                    <div class="mc-card-header">
                        <h3 class="flex items-center gap-2">
                            <i data-lucide="building-2" class="w-4 h-4 text-[#323338]/60"></i>
                            Locations
                        </h3>
                        <span class="text-xs text-gray-400">${Array.isArray(locs) ? locs.length : 0} locations</span>
                    </div>
                    <div class="mc-card-body p-0">
                        <div class="overflow-x-auto">
                            <table class="mc-table">
                                <thead>
                                    <tr>
                                        <th>Company</th>
                                        <th>Address</th>
                                        <th>Phone</th>
                                        <th>Status</th>
                                        <th class="text-right">Views</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Array.isArray(locs) && locs.length ? locs.map(l => `
                                    <tr>
                                        <td class="font-medium text-[#323338]">${this._esc(l.name || l.company || '')}</td>
                                        <td class="text-gray-600">${this._esc(l.address || '')}</td>
                                        <td class="text-gray-600">${this._esc(l.phone || '')}</td>
                                        <td><span class="badge ${l.verified ? 'badge-active' : 'badge-expiring'}">${l.verified ? 'Verified' : 'Pending'}</span></td>
                                        <td class="deal-value">${this._fmt(l.views || 0)}</td>
                                    </tr>`).join('') : `<tr><td colspan="5"><div class="empty-state"><i data-lucide="map" class="empty-state-icon"></i><p class="empty-state-title">No locations found</p><p class="empty-state-text">Connect your Google Business Profile to see location data.</p></div></td></tr>`}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>`;

            if (window.lucide) lucide.createIcons();
        } catch (err) {
            container.innerHTML = `<div class="mc-card"><div class="empty-state"><i data-lucide="alert-triangle" class="empty-state-icon"></i><p class="empty-state-title">Failed to load GBP data</p><p class="empty-state-text">${this._esc(err.message)}</p></div></div>`;
            if (window.lucide) lucide.createIcons();
        }
    },

    _fmt(n) { return Number(n).toLocaleString(); },
    _esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
};
