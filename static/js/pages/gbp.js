/**
 * Mission Control — Google Business Profile Page
 */
window.PageGBP = {
    async render(company) {
        const container = document.getElementById('page-gbp');
        if (!container) return;

        container.innerHTML = `<div class="page-enter"><div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}</div></div>`;

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
                    <div class="mc-card text-center">
                        <div class="flex items-center justify-center gap-2 mb-1"><i data-lucide="eye" class="w-4 h-4 text-blue-600"></i></div>
                        <div class="text-2xl font-bold text-navy">${this._fmt(totals.views || 0)}</div>
                        <div class="text-xs text-gray-500 mt-1">Total Views</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="flex items-center justify-center gap-2 mb-1"><i data-lucide="mouse-pointer-click" class="w-4 h-4 text-green-600"></i></div>
                        <div class="text-2xl font-bold text-navy">${this._fmt(totals.clicks || 0)}</div>
                        <div class="text-xs text-gray-500 mt-1">Clicks</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="flex items-center justify-center gap-2 mb-1"><i data-lucide="phone" class="w-4 h-4 text-amber-600"></i></div>
                        <div class="text-2xl font-bold text-navy">${this._fmt(totals.calls || 0)}</div>
                        <div class="text-xs text-gray-500 mt-1">Calls</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="flex items-center justify-center gap-2 mb-1"><i data-lucide="map-pin" class="w-4 h-4 text-red-600"></i></div>
                        <div class="text-2xl font-bold text-navy">${this._fmt(totals.directions || 0)}</div>
                        <div class="text-xs text-gray-500 mt-1">Directions</div>
                    </div>
                </div>

                <!-- Locations -->
                <div class="mc-card">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-lg font-semibold text-navy flex items-center gap-2">
                            <i data-lucide="building-2" class="w-5 h-5"></i> Locations
                        </h2>
                        <span class="mc-badge mc-badge-info">${Array.isArray(locs) ? locs.length : 0} locations</span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="mc-table">
                            <thead>
                                <tr>
                                    <th>Company</th>
                                    <th>Address</th>
                                    <th>Phone</th>
                                    <th>Status</th>
                                    <th>Views</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Array.isArray(locs) && locs.length ? locs.map(l => `
                                <tr>
                                    <td class="font-medium text-navy">${this._esc(l.name || l.company || '')}</td>
                                    <td class="text-gray-600">${this._esc(l.address || '')}</td>
                                    <td class="text-gray-600">${this._esc(l.phone || '')}</td>
                                    <td><span class="mc-badge ${l.verified ? 'mc-badge-success' : 'mc-badge-warning'}">${l.verified ? 'Verified' : 'Pending'}</span></td>
                                    <td class="text-gray-600">${this._fmt(l.views || 0)}</td>
                                </tr>`).join('') : `<tr><td colspan="5"><div class="empty-state"><i data-lucide="map" class="empty-state-icon"></i><p class="empty-state-title">No locations found</p><p class="empty-state-text">Connect your Google Business Profile to see location data.</p></div></td></tr>`}
                            </tbody>
                        </table>
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
