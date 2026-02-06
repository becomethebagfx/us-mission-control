/**
 * Mission Control — Brand Consistency Audit Page
 */
window.PageBrandAudit = {
    async render(company) {
        const container = document.getElementById('page-brand-audit');
        if (!container) return;

        container.innerHTML = `<div class="page-enter"><div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}</div></div>`;

        try {
            const [audits, summary] = await Promise.all([
                API.brandAudit.list(),
                API.brandAudit.summary(),
            ]);

            const items = audits.audits || audits || [];
            const sum = summary.summary || summary || {};

            container.innerHTML = `<div class="page-enter">
                <!-- Overall Score -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="mc-card text-center">
                        <div class="text-3xl font-bold ${(sum.overall_score || 0) >= 80 ? 'text-green-600' : (sum.overall_score || 0) >= 60 ? 'text-amber-600' : 'text-red-600'}">${sum.overall_score || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Overall Score</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${sum.nap_score || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">NAP Consistency</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${sum.visual_score || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Visual Brand</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${sum.voice_score || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Brand Voice</div>
                    </div>
                </div>

                <!-- Company Audits -->
                <div class="mc-card">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-lg font-semibold text-navy flex items-center gap-2">
                            <i data-lucide="shield-check" class="w-5 h-5"></i> Company Brand Health
                        </h2>
                    </div>
                    <div class="space-y-4">
                        ${Array.isArray(items) && items.length ? items.map(a => `
                        <div class="border border-gray-100 rounded-xl p-5 hover:border-gray-200 transition-colors">
                            <div class="flex items-center justify-between mb-3">
                                <span class="font-semibold text-navy">${this._esc(a.company || '')}</span>
                                <span class="mc-badge ${(a.score || 0) >= 80 ? 'mc-badge-success' : (a.score || 0) >= 60 ? 'mc-badge-warning' : 'mc-badge-danger'}">${a.score || 0}/100</span>
                            </div>
                            <div class="grid grid-cols-3 gap-4 text-center text-sm">
                                <div>
                                    <div class="text-xs text-gray-400 mb-1">NAP</div>
                                    <div class="font-semibold text-navy">${a.nap_score || 0}</div>
                                </div>
                                <div>
                                    <div class="text-xs text-gray-400 mb-1">Visual</div>
                                    <div class="font-semibold text-navy">${a.visual_score || 0}</div>
                                </div>
                                <div>
                                    <div class="text-xs text-gray-400 mb-1">Voice</div>
                                    <div class="font-semibold text-navy">${a.voice_score || 0}</div>
                                </div>
                            </div>
                            ${a.issues && a.issues.length ? `
                            <div class="mt-3 pt-3 border-t border-gray-50">
                                <p class="text-xs text-gray-400 mb-2">Issues (${a.issues.length}):</p>
                                ${a.issues.slice(0, 3).map(i => `<p class="text-xs text-gray-500 mb-1">• ${this._esc(i.description || i)}</p>`).join('')}
                            </div>` : ''}
                        </div>`).join('') : `<div class="empty-state"><i data-lucide="shield-check" class="empty-state-icon"></i><p class="empty-state-title">No audits run</p><p class="empty-state-text">Run a brand consistency audit to see results here.</p></div>`}
                    </div>
                </div>
            </div>`;

            if (window.lucide) lucide.createIcons();
        } catch (err) {
            container.innerHTML = `<div class="mc-card"><div class="empty-state"><i data-lucide="alert-triangle" class="empty-state-icon"></i><p class="empty-state-title">Failed to load brand audit</p><p class="empty-state-text">${this._esc(err.message)}</p></div></div>`;
            if (window.lucide) lucide.createIcons();
        }
    },

    _esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
};
