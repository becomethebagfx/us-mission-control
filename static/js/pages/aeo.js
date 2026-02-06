/**
 * Mission Control — AEO/GEO Engine Page
 * Premium redesign: stat-card pattern, mc-card-header/body, breathing room.
 */
window.PageAEO = {
    async render(company) {
        const container = document.getElementById('page-aeo');
        if (!container) return;

        container.innerHTML = `
            <div class="page-enter">
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}
                </div>
                <div class="skeleton" style="height:320px;border-radius:12px"></div>
            </div>`;

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
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${st.total_queries || qs.length || 0}</div>
                                <div class="stat-label">Target Queries</div>
                            </div>
                            <div class="stat-icon bg-blue-50">
                                <i data-lucide="search" class="w-5 h-5 text-blue-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${st.capsules_generated || 0}</div>
                                <div class="stat-label">Capsules Generated</div>
                            </div>
                            <div class="stat-icon bg-emerald-50">
                                <i data-lucide="file-check" class="w-5 h-5 text-emerald-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="${(st.avg_score || 0) >= 70 ? 'text-green-600' : (st.avg_score || 0) >= 40 ? 'text-amber-600' : 'text-navy'} text-2xl font-bold">${st.avg_score ? st.avg_score.toFixed(0) : 0}</div>
                                <div class="stat-label">Avg AEO Score</div>
                            </div>
                            <div class="stat-icon bg-amber-50">
                                <i data-lucide="brain" class="w-5 h-5 text-amber-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${st.citations || 0}</div>
                                <div class="stat-label">Est. Citations</div>
                            </div>
                            <div class="stat-icon bg-violet-50">
                                <i data-lucide="quote" class="w-5 h-5 text-violet-600"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Queries Table -->
                <div class="mc-card">
                    <div class="mc-card-header">
                        <h3 class="flex items-center gap-2">
                            <i data-lucide="search" class="w-4 h-4 text-navy/60"></i>
                            Target Queries
                        </h3>
                        <span class="text-xs text-gray-400">${Array.isArray(qs) ? qs.length : 0} queries</span>
                    </div>
                    <div class="mc-card-body p-0">
                        <div class="overflow-x-auto">
                            <table class="mc-table">
                                <thead>
                                    <tr>
                                        <th>Query</th>
                                        <th>Company</th>
                                        <th>Category</th>
                                        <th>Difficulty</th>
                                        <th class="text-center">Score</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${Array.isArray(qs) && qs.length ? qs.map(q => `
                                    <tr>
                                        <td class="font-medium text-navy">${this._esc(q.query || q.text || '')}</td>
                                        <td><span class="badge badge-scheduled">${this._esc(q.company || '')}</span></td>
                                        <td class="text-gray-600">${this._esc(q.category || q.intent || '')}</td>
                                        <td>
                                            <div class="flex items-center gap-2">
                                                <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                                                    <div class="h-full rounded-full ${(q.difficulty || 0) > 50 ? 'bg-red-400' : 'bg-green-400'}" style="width:${q.difficulty || 0}%"></div>
                                                </div>
                                                <span class="text-xs text-gray-500">${q.difficulty || 0}</span>
                                            </div>
                                        </td>
                                        <td class="text-center">
                                            <span class="score-badge ${(q.score || 0) >= 80 ? 'score-badge-green' : (q.score || 0) >= 60 ? 'score-badge-blue' : (q.score || 0) >= 40 ? 'score-badge-amber' : 'score-badge-red'}">${q.score || 0}</span>
                                        </td>
                                    </tr>`).join('') : `<tr><td colspan="5"><div class="empty-state"><i data-lucide="search" class="empty-state-icon"></i><p class="empty-state-title">No queries tracked</p><p class="empty-state-text">Add target queries to track AEO performance.</p></div></td></tr>`}
                                </tbody>
                            </table>
                        </div>
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
