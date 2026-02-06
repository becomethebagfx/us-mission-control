/**
 * Mission Control — Review Management Page
 * Premium redesign: stat-card pattern, mc-card-header/body, star ratings, breathing room.
 */
window.PageReviews = {
    async render(company) {
        const container = document.getElementById('page-reviews');
        if (!container) return;

        container.innerHTML = `
            <div class="page-enter">
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    ${Array(4).fill('<div class="skeleton skeleton-card"></div>').join('')}
                </div>
                <div class="skeleton" style="height:400px;border-radius:12px"></div>
            </div>`;

        try {
            const [reviews, summary] = await Promise.all([
                API.reviews.list(),
                API.reviews.summary(),
            ]);

            const items = reviews.reviews || reviews || [];
            const sum = summary.summary || summary || {};

            const avgColor = (sum.avg_rating || 0) >= 4.0 ? 'text-green-600' : (sum.avg_rating || 0) >= 3.0 ? 'text-amber-600' : 'text-red-600';
            const sentColor = (sum.avg_sentiment || 0) > 0 ? 'text-green-600' : (sum.avg_sentiment || 0) < 0 ? 'text-red-600' : 'text-gray-600';

            container.innerHTML = `<div class="page-enter">
                <!-- Stats -->
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${sum.total || items.length || 0}</div>
                                <div class="stat-label">Total Reviews</div>
                            </div>
                            <div class="stat-icon bg-blue-50">
                                <i data-lucide="message-square" class="w-5 h-5 text-blue-600"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="${avgColor} text-2xl font-bold">${sum.avg_rating ? sum.avg_rating.toFixed(1) : '0.0'}</div>
                                <div class="stat-label">Avg Rating</div>
                            </div>
                            <div class="stat-icon bg-amber-50">
                                <i data-lucide="star" class="w-5 h-5 text-amber-500"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="stat-value">${sum.pending_replies || 0}</div>
                                <div class="stat-label">Pending Replies</div>
                            </div>
                            <div class="stat-icon bg-red-50">
                                <i data-lucide="clock" class="w-5 h-5 text-red-500"></i>
                            </div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="${sentColor} text-2xl font-bold">${sum.avg_sentiment ? (sum.avg_sentiment > 0 ? '+' : '') + sum.avg_sentiment.toFixed(2) : '0.00'}</div>
                                <div class="stat-label">Avg Sentiment</div>
                            </div>
                            <div class="stat-icon bg-emerald-50">
                                <i data-lucide="trending-up" class="w-5 h-5 text-emerald-600"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Reviews List -->
                <div class="mc-card">
                    <div class="mc-card-header">
                        <h3 class="flex items-center gap-2">
                            <i data-lucide="star" class="w-4 h-4 text-navy/60"></i>
                            Recent Reviews
                        </h3>
                        <span class="text-xs text-gray-400">${Array.isArray(items) ? items.length : 0} reviews</span>
                    </div>
                    <div class="mc-card-body">
                        <div class="space-y-4">
                            ${Array.isArray(items) && items.length ? items.slice(0, 15).map(r => `
                            <div class="border border-gray-100 rounded-xl p-4 hover:border-gray-200 transition-colors">
                                <div class="flex items-start justify-between mb-2">
                                    <div class="flex items-center gap-2">
                                        <span class="font-medium text-navy text-sm">${this._esc(r.author || r.reviewer || 'Anonymous')}</span>
                                        <span class="badge badge-scheduled">${this._esc(r.company || '')}</span>
                                    </div>
                                    <div class="flex items-center gap-1.5">
                                        ${this._stars(r.rating || 0)}
                                        <span class="text-xs text-gray-400 ml-1">${this._esc(r.platform || 'Google')}</span>
                                    </div>
                                </div>
                                <p class="text-sm text-gray-600 leading-relaxed mb-2">${this._esc(r.text || r.content || '')}</p>
                                ${r.reply ? `
                                <div class="bg-gray-50 rounded-lg p-3 mt-2">
                                    <p class="text-xs text-gray-500 font-medium mb-1">Reply:</p>
                                    <p class="text-sm text-gray-600">${this._esc(r.reply)}</p>
                                </div>` : `<span class="badge badge-expiring">Needs Reply</span>`}
                            </div>`).join('') : `
                            <div class="empty-state">
                                <i data-lucide="star" class="empty-state-icon"></i>
                                <p class="empty-state-title">No reviews yet</p>
                                <p class="empty-state-text">Reviews will appear here once connected to review platforms.</p>
                            </div>`}
                        </div>
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
        return Array.from({length: 5}, (_, i) =>
            `<i data-lucide="star" class="w-3.5 h-3.5 ${i < n ? 'text-amber-400 fill-amber-400' : 'text-gray-200'}"></i>`
        ).join('');
    },
    _esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; },
};
