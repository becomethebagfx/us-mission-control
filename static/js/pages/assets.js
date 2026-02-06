/**
 * Mission Control — Visual Assets Page
 * Premium redesign: stat-card pattern, mc-card-header/body, asset grid with breathing room.
 */
window.PageAssets = {
    async render(company) {
        const container = document.getElementById('page-assets');
        if (!container) return;

        container.innerHTML = `
            <div class="page-enter">
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}
                </div>
                <div class="skeleton" style="height:400px;border-radius:12px"></div>
            </div>`;

        try {
            const [assets, stats] = await Promise.all([
                API.assets.list(company),
                API.assets.stats(),
            ]);

            const items = assets.assets || assets || [];
            const st = stats.stats || stats || {};

            container.innerHTML = `<div class="page-enter">
                <!-- Stats -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${st.total || items.length || 0}</div>
                                <div class="stat-label">Total Assets</div>
                            </div>
                            <div class="stat-icon bg-blue-50">
                                <i data-lucide="image" class="w-5 h-5 text-blue-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${st.templates || 0}</div>
                                <div class="stat-label">Templates</div>
                            </div>
                            <div class="stat-icon bg-violet-50">
                                <i data-lucide="layout-template" class="w-5 h-5 text-violet-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${st.social_cards || 0}</div>
                                <div class="stat-label">Social Cards</div>
                            </div>
                            <div class="stat-icon bg-emerald-50">
                                <i data-lucide="share-2" class="w-5 h-5 text-emerald-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${st.showcases || 0}</div>
                                <div class="stat-label">Showcases</div>
                            </div>
                            <div class="stat-icon bg-amber-50">
                                <i data-lucide="award" class="w-5 h-5 text-amber-600"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Asset Grid -->
                <div class="mc-card">
                    <div class="mc-card-header">
                        <h3 class="flex items-center gap-2">
                            <i data-lucide="image" class="w-4 h-4 text-navy/60"></i>
                            Asset Library
                        </h3>
                        <span class="text-xs text-gray-400">${Array.isArray(items) ? items.length : 0} assets</span>
                    </div>
                    <div class="mc-card-body">
                        ${Array.isArray(items) && items.length ? `
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            ${items.slice(0, 12).map(a => `
                            <div class="border border-gray-100 rounded-xl overflow-hidden hover:border-gray-200 hover:shadow-sm transition-all">
                                <div class="aspect-video bg-gray-50 flex items-center justify-center">
                                    ${a.thumbnail ? `<img src="${this._esc(a.thumbnail)}" class="w-full h-full object-cover" alt="${this._esc(a.name || '')}">` : `<i data-lucide="image" class="w-8 h-8 text-gray-300"></i>`}
                                </div>
                                <div class="p-4">
                                    <p class="font-medium text-navy text-sm truncate">${this._esc(a.name || a.title || 'Untitled')}</p>
                                    <div class="flex items-center gap-2 mt-2">
                                        <span class="badge badge-generated">${this._esc(a.type || 'asset')}</span>
                                        <span class="badge badge-scheduled">${this._esc(a.company || '')}</span>
                                        ${a.platform ? `<span class="text-xs text-gray-400">${this._esc(a.platform)}</span>` : ''}
                                    </div>
                                    ${a.dimensions ? `<p class="text-xs text-gray-400 mt-2">${this._esc(a.dimensions)}</p>` : ''}
                                </div>
                            </div>`).join('')}
                        </div>` : `
                        <div class="empty-state">
                            <i data-lucide="image" class="empty-state-icon"></i>
                            <p class="empty-state-title">No assets generated</p>
                            <p class="empty-state-text">Generate visual assets from templates to see them here.</p>
                        </div>`}
                    </div>
                </div>
            </div>`;

            if (window.lucide) lucide.createIcons();
        } catch (err) {
            container.innerHTML = `<div class="mc-card"><div class="empty-state"><i data-lucide="alert-triangle" class="empty-state-icon"></i><p class="empty-state-title">Failed to load assets</p><p class="empty-state-text">${this._esc(err.message)}</p></div></div>`;
            if (window.lucide) lucide.createIcons();
        }
    },

    _esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
};
