/**
 * Mission Control — Brand Consistency Audit Page
 * Premium redesign: stat-card pattern, color-coded scores, mc-card-header/body.
 */
window.PageBrandAudit = {
    async render(company) {
        const container = document.getElementById('page-brand-audit');
        if (!container) return;

        container.innerHTML = `
            <div class="page-enter">
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}
                </div>
                <div class="skeleton" style="height:400px;border-radius:12px"></div>
            </div>`;

        try {
            const [audits, summary] = await Promise.all([
                API.brandAudit.list(),
                API.brandAudit.summary(),
            ]);

            const items = audits.audits || audits || [];
            const sum = summary.summary || summary || {};

            const scoreColor = (s) => (s || 0) >= 80 ? 'text-green-600' : (s || 0) >= 60 ? 'text-amber-600' : 'text-red-600';
            const scoreBg = (s) => (s || 0) >= 80 ? 'bg-green-50' : (s || 0) >= 60 ? 'bg-amber-50' : 'bg-red-50';

            container.innerHTML = `<div class="page-enter">
                <!-- Overall Score -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="${scoreColor(sum.overall_score)} text-3xl font-bold">${sum.overall_score || 0}</div>
                                <div class="stat-label">Overall Score</div>
                            </div>
                            <div class="stat-icon ${scoreBg(sum.overall_score)}">
                                <i data-lucide="shield-check" class="w-5 h-5 ${scoreColor(sum.overall_score)}"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${sum.nap_score || 0}</div>
                                <div class="stat-label">NAP Consistency</div>
                            </div>
                            <div class="stat-icon bg-blue-50">
                                <i data-lucide="map-pin" class="w-5 h-5 text-blue-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${sum.visual_score || 0}</div>
                                <div class="stat-label">Visual Brand</div>
                            </div>
                            <div class="stat-icon bg-violet-50">
                                <i data-lucide="palette" class="w-5 h-5 text-violet-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${sum.voice_score || 0}</div>
                                <div class="stat-label">Brand Voice</div>
                            </div>
                            <div class="stat-icon bg-emerald-50">
                                <i data-lucide="megaphone" class="w-5 h-5 text-emerald-600"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Company Audits -->
                <div class="mc-card">
                    <div class="mc-card-header">
                        <h3 class="flex items-center gap-2">
                            <i data-lucide="shield-check" class="w-4 h-4 text-[#323338]/60"></i>
                            Company Brand Health
                        </h3>
                        <span class="text-xs text-gray-400">${Array.isArray(items) ? items.length : 0} audits</span>
                    </div>
                    <div class="mc-card-body">
                        <div class="space-y-4">
                            ${Array.isArray(items) && items.length ? items.map(a => `
                            <div class="border border-gray-100 rounded-xl p-5 hover:border-gray-200 transition-colors">
                                <div class="flex items-center justify-between mb-3">
                                    <span class="font-semibold text-[#323338]">${this._esc(a.company || '')}</span>
                                    <span class="score-badge ${(a.score || 0) >= 80 ? 'score-badge-green' : (a.score || 0) >= 60 ? 'score-badge-amber' : 'score-badge-red'}">${a.score || 0}</span>
                                </div>
                                <div class="grid grid-cols-3 gap-4 text-center text-sm">
                                    <div>
                                        <div class="text-xs text-gray-400 mb-1">NAP</div>
                                        <div class="font-semibold text-[#323338]">${a.nap_score || 0}</div>
                                    </div>
                                    <div>
                                        <div class="text-xs text-gray-400 mb-1">Visual</div>
                                        <div class="font-semibold text-[#323338]">${a.visual_score || 0}</div>
                                    </div>
                                    <div>
                                        <div class="text-xs text-gray-400 mb-1">Voice</div>
                                        <div class="font-semibold text-[#323338]">${a.voice_score || 0}</div>
                                    </div>
                                </div>
                                ${a.issues && a.issues.length ? `
                                <div class="mt-3 pt-3 border-t border-gray-50">
                                    <p class="text-xs text-gray-400 mb-2">Issues (${a.issues.length}):</p>
                                    ${a.issues.slice(0, 3).map(i => `<p class="text-xs text-gray-500 mb-1">${this._esc(i.description || i)}</p>`).join('')}
                                </div>` : ''}
                            </div>`).join('') : `
                            <div class="empty-state">
                                <i data-lucide="shield-check" class="empty-state-icon"></i>
                                <p class="empty-state-title">No audits run</p>
                                <p class="empty-state-text">Run a brand consistency audit to see results here.</p>
                            </div>`}
                        </div>
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
