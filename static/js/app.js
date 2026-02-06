/**
 * Mission Control — Alpine.js Application
 * Hash-based routing, company filter, page initialization.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('dashboard', () => ({
        // State
        currentPage: 'home',
        activeCompany: '',
        sidebarOpen: false,
        pageTitle: 'Dashboard',
        pageSubtitle: 'Overview of all marketing systems',

        // Companies registry
        companies: {
            us_construction: { name: 'US Construction', slug: 'us-construction', color: '#1B2A4A', accent: 'navy' },
            us_framing: { name: 'US Framing', slug: 'us-framing', color: '#579BFC', accent: 'blue' },
            us_drywall: { name: 'US Drywall', slug: 'us-drywall', color: '#FDAB3D', accent: 'amber' },
            us_interiors: { name: 'US Interiors', slug: 'us-interiors', color: '#5B7B99', accent: 'slate' },
            us_exteriors: { name: 'US Exteriors', slug: 'us-exteriors', color: '#00C875', accent: 'green' },
            us_development: { name: 'US Development', slug: 'us-development', color: '#C4AF94', accent: 'tan' },
        },

        // Navigation items
        navItems: [
            { page: 'home', hash: '#home', label: 'Dashboard', icon: 'layout-dashboard' },
            { page: 'calendar', hash: '#calendar', label: 'Calendar', icon: 'calendar' },
            { page: 'content', hash: '#content', label: 'Content Library', icon: 'file-text' },
            { page: 'gbp', hash: '#gbp', label: 'Google Business', icon: 'map-pin' },
            { page: 'aeo', hash: '#aeo', label: 'AEO/GEO Engine', icon: 'search' },
            { page: 'reviews', hash: '#reviews', label: 'Reviews', icon: 'star' },
            { page: 'brand-audit', hash: '#brand-audit', label: 'Brand Audit', icon: 'shield-check' },
            { page: 'assets', hash: '#assets', label: 'Visual Assets', icon: 'image' },
            { page: 'quality', hash: '#quality', label: 'Quality Loop', icon: 'refresh-cw' },
            { page: 'reactivation', hash: '#reactivation', label: 'Reactivation', icon: 'users' },
            { page: 'settings', hash: '#settings', label: 'Settings', icon: 'settings' },
        ],

        // Page metadata
        pageMeta: {
            home: { title: 'Dashboard', subtitle: 'Overview of all marketing systems' },
            calendar: { title: 'LinkedIn Calendar', subtitle: 'Scheduled posts and events' },
            'post-detail': { title: 'Post Detail', subtitle: 'Review and manage post' },
            content: { title: 'Content Library', subtitle: 'Articles and content management' },
            gbp: { title: 'Google Business Profile', subtitle: 'Locations, insights, and local search' },
            aeo: { title: 'AEO/GEO Engine', subtitle: 'Answer engine optimization and AI citations' },
            reviews: { title: 'Review Management', subtitle: 'Monitor and respond to customer reviews' },
            'brand-audit': { title: 'Brand Consistency', subtitle: 'NAP accuracy, visual identity, and voice' },
            assets: { title: 'Visual Assets', subtitle: 'Templates, social cards, and showcases' },
            quality: { title: 'Quality Loop', subtitle: 'Recursive content improvement engine' },
            reactivation: { title: 'Database Reactivation', subtitle: 'Lead pipeline and sequences' },
            settings: { title: 'Settings', subtitle: 'OAuth tokens, companies, and system info' },
        },

        // Init
        init() {
            this.handleRoute();
            window.addEventListener('hashchange', () => this.handleRoute());

            // Re-render Lucide icons after Alpine renders
            this.$nextTick(() => {
                if (window.lucide) lucide.createIcons();
            });
        },

        // Hash router
        handleRoute() {
            const hash = window.location.hash.slice(1) || 'home';
            const parts = hash.split('/');
            const page = parts[0];

            // Store route params for pages
            this._routeParams = parts.slice(1);

            if (this.pageMeta[page]) {
                this.currentPage = page;
                this.pageTitle = this.pageMeta[page].title;
                this.pageSubtitle = this.pageMeta[page].subtitle;
            } else {
                this.currentPage = 'home';
                this.pageTitle = this.pageMeta.home.title;
                this.pageSubtitle = this.pageMeta.home.subtitle;
            }

            // Trigger page load with fade transition
            const container = document.getElementById('page-container');
            if (container) {
                container.classList.remove('page-fade-active');
                container.classList.add('page-fade-enter');
            }
            this.$nextTick(() => {
                this.loadPage(this.currentPage).then(() => {
                    if (window.lucide) lucide.createIcons();
                    // Fade in after render
                    requestAnimationFrame(() => {
                        if (container) {
                            container.classList.remove('page-fade-enter');
                            container.classList.add('page-fade-active');
                        }
                    });
                });
            });
        },

        // Get active company color for indicator
        getActiveCompanyColor() {
            if (!this.activeCompany) return 'transparent';
            const key = Object.keys(this.companies).find(k => this.companies[k].slug === this.activeCompany);
            return key ? this.companies[key].color : 'transparent';
        },

        // Company filter change
        onCompanyChange() {
            this.loadPage(this.currentPage);
        },

        // Load page data and render
        async loadPage(page) {
            const company = this.activeCompany || null;
            try {
                switch (page) {
                    case 'home':
                        if (window.PageHome) await PageHome.render(company);
                        break;
                    case 'calendar':
                        if (window.PageCalendar) await PageCalendar.render(company);
                        break;
                    case 'post-detail':
                        if (window.PagePostDetail) await PagePostDetail.render(this._routeParams[0]);
                        break;
                    case 'content':
                        if (window.PageContent) await PageContent.render(company);
                        break;
                    case 'gbp':
                        if (window.PageGBP) await PageGBP.render(company);
                        break;
                    case 'aeo':
                        if (window.PageAEO) await PageAEO.render(company);
                        break;
                    case 'reviews':
                        if (window.PageReviews) await PageReviews.render(company);
                        break;
                    case 'brand-audit':
                        if (window.PageBrandAudit) await PageBrandAudit.render(company);
                        break;
                    case 'assets':
                        if (window.PageAssets) await PageAssets.render(company);
                        break;
                    case 'quality':
                        if (window.PageQuality) await PageQuality.render(company);
                        break;
                    case 'reactivation':
                        if (window.PageReactivation) await PageReactivation.render(company);
                        break;
                    case 'settings':
                        if (window.PageSettings) await PageSettings.render();
                        break;
                }
            } catch (err) {
                console.error(`Error loading page ${page}:`, err);
            }
        },
    }));
});
