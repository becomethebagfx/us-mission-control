/**
 * Mission Control — Content Library Page
 * Premium redesign: skeleton loading, consistent cards, breathing room.
 */
window.PageContent = {
    container: null,
    _articles: [],
    _stats: null,
    _filterStatus: '',
    _searchQuery: '',
    _selectedArticle: null,

    async render(company) {
        this.container = document.getElementById('page-content');
        if (!this.container) return;

        this.container.innerHTML = this._renderLoading();

        try {
            const [stats, articles] = await Promise.all([
                API.content.stats(company),
                API.content.list(company, null),
            ]);
            this._stats = stats;
            this._articles = articles;
            this._filterStatus = '';
            this._searchQuery = '';
            this._selectedArticle = null;
            this._company = company;
            this._renderPage();
        } catch (err) {
            console.error('PageContent load error:', err);
            this.container.innerHTML = this._renderError(err.message);
            if (window.lucide) lucide.createIcons();
        }
    },

    _renderLoading() {
        return `
            <div class="page-enter">
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
                    ${Array(6).fill('<div class="skeleton skeleton-card" style="height:88px"></div>').join('')}
                </div>
                <div class="skeleton" style="height:56px;border-radius:12px;margin-bottom:24px"></div>
                <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                    ${Array(6).fill('<div class="skeleton" style="height:220px;border-radius:12px"></div>').join('')}
                </div>
            </div>
        `;
    },

    _renderError(message) {
        return `
            <div class="page-enter">
                <div class="mc-card">
                    <div class="empty-state">
                        <i data-lucide="alert-circle" class="empty-state-icon"></i>
                        <p class="empty-state-title">Failed to load content</p>
                        <p class="empty-state-text">${this._esc(message)}</p>
                    </div>
                </div>
            </div>
        `;
    },

    _renderPage() {
        const filtered = this._getFilteredArticles();
        const stats = this._stats || {};

        this.container.innerHTML = `
            <div class="page-enter">
                <!-- Stats Bar -->
                ${this._renderStatsBar(stats)}

                <!-- Filter Bar -->
                ${this._renderFilterBar()}

                <!-- Main Content Area -->
                <div class="flex gap-6 mt-6">
                    <!-- Article Grid -->
                    <div class="flex-1">
                        ${filtered.length > 0 ? `
                            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" id="ct-article-grid">
                                ${filtered.map(article => this._renderArticleCard(article)).join('')}
                            </div>
                            <div class="mt-4 text-xs text-gray-400 text-center">
                                Showing ${filtered.length} of ${this._articles.length} articles
                            </div>
                        ` : `
                            <div class="mc-card">
                                <div class="empty-state">
                                    <i data-lucide="file-search" class="empty-state-icon"></i>
                                    <p class="empty-state-title">No articles found</p>
                                    <p class="empty-state-text">Try adjusting your filters or search query.</p>
                                </div>
                            </div>
                        `}
                    </div>

                    <!-- Detail Panel (shown when article selected) -->
                    <div id="ct-detail-panel" class="${this._selectedArticle ? '' : 'hidden'} w-full lg:max-w-[380px] flex-shrink-0">
                        ${this._selectedArticle ? this._renderDetailPanel(this._selectedArticle) : ''}
                    </div>
                </div>
            </div>
        `;

        if (window.lucide) lucide.createIcons();
        this._bindEvents();
    },

    _renderStatsBar(stats) {
        const total = stats.total || 0;
        const byStatus = stats.by_status || {};
        const avgAeo = stats.avg_aeo_score != null ? Math.round(stats.avg_aeo_score) : '--';
        const aeoColor = typeof avgAeo === 'number' ? (avgAeo > 70 ? 'text-green-600' : avgAeo >= 40 ? 'text-yellow-600' : 'text-red-600') : 'text-gray-400';

        return `
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value">${total}</div>
                            <div class="stat-label">Total Articles</div>
                        </div>
                        <div class="stat-icon bg-navy/10">
                            <i data-lucide="file-text" class="w-5 h-5 text-[#323338]"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value">${byStatus.draft || 0}</div>
                            <div class="stat-label">Drafts</div>
                        </div>
                        <div class="stat-icon bg-gray-100">
                            <i data-lucide="edit-3" class="w-5 h-5 text-gray-500"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value">${byStatus.review || 0}</div>
                            <div class="stat-label">In Review</div>
                        </div>
                        <div class="stat-icon bg-yellow-50">
                            <i data-lucide="eye" class="w-5 h-5 text-yellow-600"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value">${byStatus.approved || 0}</div>
                            <div class="stat-label">Approved</div>
                        </div>
                        <div class="stat-icon bg-emerald-50">
                            <i data-lucide="check-circle" class="w-5 h-5 text-emerald-600"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="stat-value">${byStatus.published || 0}</div>
                            <div class="stat-label">Published</div>
                        </div>
                        <div class="stat-icon bg-green-50">
                            <i data-lucide="globe" class="w-5 h-5 text-green-600"></i>
                        </div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="${aeoColor} text-2xl font-bold">${avgAeo}${typeof avgAeo === 'number' ? '%' : ''}</div>
                            <div class="stat-label">Avg AEO Score</div>
                        </div>
                        <div class="stat-icon bg-blue-50">
                            <i data-lucide="brain" class="w-5 h-5 text-blue-600"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    _renderFilterBar() {
        return `
            <div class="mc-card">
                <div class="mc-card-body" style="padding:1rem 1.5rem">
                    <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                        <!-- Status Filter -->
                        <div class="flex items-center gap-2">
                            <i data-lucide="filter" class="w-4 h-4 text-gray-400"></i>
                            <select id="ct-status-filter"
                                class="border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:ring-2 focus:ring-navy/10 focus:border-navy/40 outline-none bg-white">
                                <option value="">All Statuses</option>
                                <option value="draft" ${this._filterStatus === 'draft' ? 'selected' : ''}>Draft</option>
                                <option value="review" ${this._filterStatus === 'review' ? 'selected' : ''}>In Review</option>
                                <option value="approved" ${this._filterStatus === 'approved' ? 'selected' : ''}>Approved</option>
                                <option value="published" ${this._filterStatus === 'published' ? 'selected' : ''}>Published</option>
                            </select>
                        </div>
                        <!-- Search -->
                        <div class="flex-1 relative">
                            <i data-lucide="search" class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2"></i>
                            <input type="text" id="ct-search-input"
                                value="${this._esc(this._searchQuery)}"
                                placeholder="Search articles by title or topic..."
                                class="w-full border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm text-gray-700 focus:ring-2 focus:ring-navy/10 focus:border-navy/40 outline-none">
                        </div>
                        <!-- Result count -->
                        <div class="text-xs text-gray-400 whitespace-nowrap self-center">
                            ${this._getFilteredArticles().length} result${this._getFilteredArticles().length !== 1 ? 's' : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    _renderArticleCard(article) {
        const companyColor = this._companyColor(article.company_slug);
        const statusPill = this._statusPill(article.status || 'draft');
        const aeoScore = article.aeo_score != null ? Math.round(article.aeo_score) : null;
        const aeoBarColor = aeoScore !== null ? (aeoScore > 70 ? 'bg-green-500' : aeoScore >= 40 ? 'bg-yellow-500' : 'bg-red-500') : 'bg-gray-200';
        const aeoTextColor = aeoScore !== null ? (aeoScore > 70 ? 'text-green-600' : aeoScore >= 40 ? 'text-yellow-600' : 'text-red-600') : 'text-gray-400';
        const tags = article.tags || [];
        const isSelected = this._selectedArticle && this._selectedArticle.id === article.id;

        return `
            <div class="mc-card cursor-pointer transition-all duration-200 ${isSelected ? 'ring-2 ring-navy/20 border-navy/30' : ''}"
                 data-article-id="${article.id}">
                <div class="mc-card-body">
                    <!-- Header -->
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex items-center gap-1.5">
                            <span class="company-dot" style="background:${companyColor}"></span>
                            <span class="text-xs text-gray-500">${this._esc(article.company || '')}</span>
                        </div>
                        ${statusPill}
                    </div>
                    <!-- Title -->
                    <h4 class="text-sm font-semibold text-[#323338] leading-snug mb-2 line-clamp-2">${this._esc(article.title || 'Untitled')}</h4>
                    ${article.topic && article.topic !== article.title ? `<p class="text-xs text-gray-500 mb-3">${this._esc(article.topic)}</p>` : ''}
                    <!-- Word Count + AEO Score -->
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs text-gray-400">
                            <i data-lucide="type" class="w-3 h-3 inline mr-0.5"></i>
                            ${article.word_count ? article.word_count.toLocaleString() + ' words' : '--'}
                        </span>
                        ${aeoScore !== null ? `
                            <span class="text-xs font-medium ${aeoTextColor}">${aeoScore}% AEO</span>
                        ` : ''}
                    </div>
                    <!-- AEO Score Bar -->
                    <div class="w-full bg-gray-100 rounded-full h-1.5 mb-3">
                        <div class="${aeoBarColor} h-1.5 rounded-full transition-all duration-500${aeoScore !== null && aeoScore > 80 ? ' shadow-[0_0_6px_rgba(34,197,94,0.5)] animate-pulse' : ''}" style="width: ${aeoScore !== null ? aeoScore : 0}%"></div>
                    </div>
                    <!-- Tags -->
                    ${tags.length > 0 ? `
                        <div class="flex flex-wrap gap-1">
                            ${tags.slice(0, 3).map(tag => `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">${this._esc(tag)}</span>`).join('')}
                            ${tags.length > 3 ? `<span class="text-xs text-gray-400">+${tags.length - 3}</span>` : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },

    _renderDetailPanel(article) {
        const companyColor = this._companyColor(article.company_slug);
        const statusPillDetail = this._statusPill(article.status || 'draft');
        const aeoScore = article.aeo_score != null ? Math.round(article.aeo_score) : null;
        const aeoBarColor = aeoScore !== null ? (aeoScore > 70 ? 'bg-green-500' : aeoScore >= 40 ? 'bg-yellow-500' : 'bg-red-500') : 'bg-gray-200';
        const aeoTextColor = aeoScore !== null ? (aeoScore > 70 ? 'text-green-600' : aeoScore >= 40 ? 'text-yellow-600' : 'text-red-600') : 'text-gray-400';
        const tags = article.tags || [];
        const isDraft = article.status === 'draft';
        const isReview = article.status === 'review';
        const isApproved = article.status === 'approved';
        const createdDate = article.created_at ? new Date(article.created_at).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        }) : '';
        const publishedDate = article.published_at ? new Date(article.published_at).toLocaleDateString('en-US', {
            year: 'numeric', month: 'short', day: 'numeric'
        }) : '';

        return `
            <div class="mc-card sticky top-24">
                <!-- Panel Header -->
                <div class="mc-card-header">
                    <h3 class="text-sm font-semibold text-[#323338]">Article Details</h3>
                    <button id="ct-close-panel" class="btn-ghost text-xs">
                        <i data-lucide="x" class="w-4 h-4"></i>
                    </button>
                </div>
                <div class="mc-card-body space-y-4">
                    <!-- Title + Company -->
                    <div>
                        <div class="flex items-center gap-1.5 mb-2">
                            <span class="company-dot" style="background:${companyColor}"></span>
                            <span class="text-xs text-gray-500">${this._esc(article.company || '')}</span>
                            <span class="ml-auto">${statusPillDetail}</span>
                        </div>
                        <h4 class="text-base font-semibold text-[#323338] leading-snug">${this._esc(article.title || 'Untitled')}</h4>
                        ${article.topic && article.topic !== article.title ? `<p class="text-xs text-gray-500 mt-1">${this._esc(article.topic)}</p>` : ''}
                    </div>

                    <!-- Meta Info -->
                    <div class="border-t border-gray-100 pt-3">
                        <dl class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <dt class="text-gray-500">Word Count</dt>
                                <dd class="text-gray-700">${article.word_count ? article.word_count.toLocaleString() : '--'}</dd>
                            </div>
                            ${createdDate ? `
                            <div class="flex justify-between">
                                <dt class="text-gray-500">Created</dt>
                                <dd class="text-gray-700">${createdDate}</dd>
                            </div>
                            ` : ''}
                            ${publishedDate ? `
                            <div class="flex justify-between">
                                <dt class="text-gray-500">Published</dt>
                                <dd class="text-gray-700">${publishedDate}</dd>
                            </div>
                            ` : ''}
                        </dl>
                    </div>

                    <!-- AEO Score -->
                    <div class="border-t border-gray-100 pt-3">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-500">AEO Score</span>
                            ${aeoScore !== null ? `
                                <span class="text-sm font-semibold ${aeoTextColor}">${aeoScore}%</span>
                            ` : `
                                <span class="text-sm text-gray-400">Not scored</span>
                            `}
                        </div>
                        <div class="w-full bg-gray-100 rounded-full h-1.5">
                            <div class="${aeoBarColor} h-1.5 rounded-full transition-all duration-500" style="width: ${aeoScore !== null ? aeoScore : 0}%"></div>
                        </div>
                        ${aeoScore !== null ? `
                            <p class="text-xs text-gray-400 mt-1">
                                ${aeoScore > 70 ? 'Strong AI Engine visibility' : aeoScore >= 40 ? 'Moderate AI Engine visibility' : 'Low AI Engine visibility - needs optimization'}
                            </p>
                        ` : ''}
                    </div>

                    <!-- Tags -->
                    ${tags.length > 0 ? `
                    <div class="border-t border-gray-100 pt-3">
                        <p class="text-xs text-gray-500 mb-2">Tags</p>
                        <div class="flex flex-wrap gap-1.5">
                            ${tags.map(tag => `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-navy/5 text-[#323338]/70">${this._esc(tag)}</span>`).join('')}
                        </div>
                    </div>
                    ` : ''}

                    <!-- Action Buttons -->
                    <div class="border-t border-gray-100 pt-3 space-y-2">
                        ${isDraft || isReview ? `
                            <button id="ct-approve-btn" data-id="${article.id}" class="w-full btn-primary">
                                <i data-lucide="check-circle" class="w-4 h-4"></i>
                                Approve Article
                            </button>
                        ` : ''}
                        ${isApproved ? `
                            <button id="ct-publish-btn" data-id="${article.id}" class="w-full btn-primary">
                                <i data-lucide="globe" class="w-4 h-4"></i>
                                Publish Article
                            </button>
                        ` : ''}
                    </div>

                    <!-- Feedback area -->
                    <div id="ct-detail-feedback" class="hidden text-center py-2">
                        <span id="ct-detail-msg" class="text-sm"></span>
                    </div>
                </div>
            </div>
        `;
    },

    _getFilteredArticles() {
        let result = this._articles || [];
        if (this._filterStatus) {
            result = result.filter(a => a.status === this._filterStatus);
        }
        if (this._searchQuery) {
            const q = this._searchQuery.toLowerCase();
            result = result.filter(a => {
                const title = (a.title || '').toLowerCase();
                const topic = (a.topic || '').toLowerCase();
                const tags = (a.tags || []).join(' ').toLowerCase();
                return title.includes(q) || topic.includes(q) || tags.includes(q);
            });
        }
        return result;
    },

    _bindEvents() {
        const container = this.container;

        const statusFilter = container.querySelector('#ct-status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this._filterStatus = e.target.value;
                this._renderPage();
            });
        }

        const searchInput = container.querySelector('#ct-search-input');
        if (searchInput) {
            let debounceTimer = null;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this._searchQuery = e.target.value;
                    this._renderPage();
                    const newInput = container.querySelector('#ct-search-input');
                    if (newInput) {
                        newInput.focus();
                        newInput.setSelectionRange(newInput.value.length, newInput.value.length);
                    }
                }, 300);
            });
        }

        const articleCards = container.querySelectorAll('[data-article-id]');
        articleCards.forEach(card => {
            card.addEventListener('click', () => {
                const id = card.dataset.articleId;
                const article = this._articles.find(a => String(a.id) === String(id));
                if (article) {
                    this._selectedArticle = article;
                    this._renderPage();
                    const panel = container.querySelector('#ct-detail-panel');
                    if (panel && window.innerWidth < 1024) {
                        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            });
        });

        const closeBtn = container.querySelector('#ct-close-panel');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this._selectedArticle = null;
                this._renderPage();
            });
        }

        const approveBtn = container.querySelector('#ct-approve-btn');
        if (approveBtn) {
            approveBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = approveBtn.dataset.id;
                approveBtn.disabled = true;
                approveBtn.textContent = 'Approving...';
                try {
                    await API.content.approve(id);
                    this._showDetailFeedback('Article approved', 'text-green-600');
                    const [stats, articles] = await Promise.all([
                        API.content.stats(this._company),
                        API.content.list(this._company, null),
                    ]);
                    this._stats = stats;
                    this._articles = articles;
                    this._selectedArticle = articles.find(a => String(a.id) === String(id)) || null;
                    setTimeout(() => this._renderPage(), 800);
                } catch (err) {
                    this._showDetailFeedback('Failed: ' + err.message, 'text-red-600');
                    approveBtn.disabled = false;
                    approveBtn.innerHTML = '<i data-lucide="check-circle" class="w-4 h-4"></i> Approve Article';
                    if (window.lucide) lucide.createIcons();
                }
            });
        }

        const publishBtn = container.querySelector('#ct-publish-btn');
        if (publishBtn) {
            publishBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = publishBtn.dataset.id;
                publishBtn.disabled = true;
                publishBtn.textContent = 'Publishing...';
                try {
                    await API.content.publish(id);
                    this._showDetailFeedback('Article published', 'text-green-600');
                    const [stats, articles] = await Promise.all([
                        API.content.stats(this._company),
                        API.content.list(this._company, null),
                    ]);
                    this._stats = stats;
                    this._articles = articles;
                    this._selectedArticle = articles.find(a => String(a.id) === String(id)) || null;
                    setTimeout(() => this._renderPage(), 800);
                } catch (err) {
                    this._showDetailFeedback('Failed: ' + err.message, 'text-red-600');
                    publishBtn.disabled = false;
                    publishBtn.innerHTML = '<i data-lucide="globe" class="w-4 h-4"></i> Publish Article';
                    if (window.lucide) lucide.createIcons();
                }
            });
        }
    },

    _showDetailFeedback(message, colorClass) {
        const fb = this.container.querySelector('#ct-detail-feedback');
        const msg = this.container.querySelector('#ct-detail-msg');
        if (fb && msg) {
            msg.textContent = message;
            msg.className = 'text-sm ' + colorClass;
            fb.classList.remove('hidden');
        }
    },

    _statusPill(status) {
        const config = {
            draft:     { bg: 'bg-gray-100',     text: 'text-gray-600',    dot: 'bg-gray-400',    label: 'Draft' },
            review:    { bg: 'bg-amber-50',     text: 'text-amber-700',   dot: 'bg-amber-400',   label: 'In Review' },
            approved:  { bg: 'bg-emerald-50',   text: 'text-emerald-700', dot: 'bg-emerald-500', label: 'Approved' },
            published: { bg: 'bg-green-50',     text: 'text-green-700',   dot: 'bg-green-500',   label: 'Published' },
        };
        const c = config[status] || config.draft;
        return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${c.bg} ${c.text}"><span class="w-1.5 h-1.5 rounded-full ${c.dot}"></span>${c.label}</span>`;
    },

    _companyColor(slug) {
        const colors = {
            'us-framing': '#579BFC',
            'us-drywall': '#FDAB3D',
            'us-exteriors': '#00C875',
            'us-development': '#C4C4C4',
        };
        return colors[slug] || '#6B7280';
    },

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },
};
