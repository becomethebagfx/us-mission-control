/**
 * Mission Control — Review Management Page
 */
window.PageReviews = {
    async render(company) {
        const container = document.getElementById('page-reviews');
        if (!container) return;

        container.innerHTML = `<div class="page-enter"><div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}</div></div>`;

        try {
            const [reviews, summary] = await Promise.all([
                API.reviews.list(),
                API.reviews.summary(),
            ]);

            const items = reviews.reviews || reviews || [];
            const sum = summary.summary || summary || {};

            container.innerHTML = `<div class="page-enter">
                <!-- Stats -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${sum.total || items.length || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Total Reviews</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${sum.avg_rating ? sum.avg_rating.toFixed(1) : '0.0'}</div>
                        <div class="text-xs text-gray-500 mt-1">Avg Rating</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${sum.pending_replies || 0}</div>
                        <div class="text-xs text-gray-500 mt-1">Pending Replies</div>
                    </div>
                    <div class="mc-card text-center">
                        <div class="text-2xl font-bold text-navy">${sum.avg_sentiment ? (sum.avg_sentiment > 0 ? '+' : '') + sum.avg_sentiment.toFixed(2) : '0.00'}</div>
                        <div class="text-xs text-gray-500 mt-1">Avg Sentiment</div>
                    </div>
                </div>

                <!-- Reviews List -->
                <div class="mc-card">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-lg font-semibold text-navy flex items-center gap-2">
                            <i data-lucide="star" class="w-5 h-5"></i> Recent Reviews
                        </h2>
                    </div>
                    <div class="space-y-4">
                        ${Array.isArray(items) && items.length ? items.slice(0, 15).map(r => `
                        <div class="border border-gray-100 rounded-xl p-4 hover:border-gray-200 transition-colors">
                            <div class="flex items-start justify-between mb-2">
                                <div>
                                    <span class="font-medium text-navy text-sm">${this._esc(r.author || r.reviewer || 'Anonymous')}</span>
                                    <span class="mc-badge mc-badge-info ml-2">${this._esc(r.company || '')}</span>
                                </div>
                                <div class="flex items-center gap-1">
                                    ${this._stars(r.rating || 0)}
                                    <span class="text-xs text-gray-400 ml-2">${r.platform || 'Google'}</span>
                                </div>
                            </div>
                            <p class="text-sm text-gray-600 mb-2">${this._esc(r.text || r.content || '')}</p>
                            ${r.reply ? `<div class="bg-gray-50 rounded-lg p-3 mt-2"><p class="text-xs text-gray-500 font-medium mb-1">Reply:</p><p class="text-sm text-gray-600">${this._esc(r.reply)}</p></div>` : `<span class="mc-badge mc-badge-warning">Needs Reply</span>`}
                        </div>`).join('') : `<div class="empty-state"><i data-lucide="star" class="empty-state-icon"></i><p class="empty-state-title">No reviews yet</p><p class="empty-state-text">Reviews will appear here once connected to review platforms.</p></div>`}
                    </div>
                </div>
            </div>`;

            if (window.lucide) lucide.createIcons();
        } catch (err) {
            container.innerHTML = `<div class="mc-card"><div class="empty-state"><i data-lucide="alert-triangle" class="empty-state-icon"></i><p class="empty-state-title">Failed to load reviews</p><p class="empty-state-text">${this._esc(err.message)}</p></div></div>`;
            if (window.lucide) lucide.createIcons();
        }
    },

    _stars(n) {
        return Array.from({length: 5}, (_, i) => `<i data-lucide="${i < n ? 'star' : 'star'}" class="w-3.5 h-3.5 ${i < n ? 'text-amber-400 fill-amber-400' : 'text-gray-200'}"></i>`).join('');
    },
    _esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
};
