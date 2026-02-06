/**
 * Mission Control — AEO/GEO Engine Page
 */
window.PageAEO = {
    async render(company) {
        const container = document.getElementById('page-aeo');
        if (!container) return;

        container.innerHTML = `<div class="page-enter"><div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}</div></div>`;

        try {
            const [queries, stats] = await Promise.all([
                API.aeo.queries(),
                API.aeo.stats(),
            ]);

            const qs = queries.queries || queries || [];
            const st = stats.stats || stats || {};

            container.innerHTML = `<div class="page-enter">
                <!-- Stats -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${st.total_queries || qs.length || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Target Queries</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${st.capsules_generated || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Capsules Generated</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${st.avg_score ? st.avg_score.toFixed(0) : 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Avg AEO Score</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${st.citations || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Est. Citations</div>
                    </div>
                </div>

                <!-- Queries Table -->
                <div class="mc-card">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-lg font-semibold text-navy flex items-center gap-2">
                            <i data-lucide="search" class="w-5 h-5"></i> Target Queries
                        </h2>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="mc-table">
                            <thead>
                                <tr>
                                    <th>Query</th>
                                    <th>Company</th>
                                    <th>Category</th>
                                    <th>Difficulty</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Array.isArray(qs) && qs.length ? qs.map(q => `
                                <tr>
                                    <td class="font-medium text-navy">${this._esc(q.query || q.text || '')}</td>
                                    <td><span class="mc-badge mc-badge-info">${this._esc(q.company || '')}</span></td>
                                    <td class="text-gray-600">${this._esc(q.category || q.intent || '')}</td>
                                    <td>
                                        <div class="flex items-center gap-2">
                                            <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                <div class="h-full rounded-full ${(q.difficulty || 0) > 50 ? 'bg-red-500' : 'bg-green-500'}" style="width:${q.difficulty || 0}%"></div>
                                            </div>
                                            <span class="text-xs text-gray-500">${q.difficulty || 0}</span>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="mc-badge ${(q.score || 0) >= 70 ? 'mc-badge-success' : (q.score || 0) >= 40 ? 'mc-badge-warning' : 'mc-badge-danger'}">${q.score || 0}</span>
                                    </td>
                                </tr>`).join('') : `<tr><td colspan="5"><div class="empty-state"><i data-lucide="search" class="empty-state-icon"></i><p class="empty-state-title">No queries tracked</p><p class="empty-state-text">Add target queries to track AEO performance.</p></div></td></tr>`}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>`;

            if (window.lucide) lucide.createIcons();
        } catch (err) {
            container.innerHTML = `<div class="mc-card"><div class="empty-state"><i data-lucide="alert-triangle" class="empty-state-icon"></i><p class="empty-state-title">Failed to load AEO data</p><p class="empty-state-text">${this._esc(err.message)}</p></div></div>`;
            if (window.lucide) lucide.createIcons();
        }
    },

    _esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
};
