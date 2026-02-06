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
            us_framing: { name: 'US Framing', slug: 'us-framing', color: '#4A90D9', accent: 'sky' },
            us_drywall: { name: 'US Drywall', slug: 'us-drywall', color: '#B8860B', accent: 'gold' },
            us_exteriors: { name: 'US Exteriors', slug: 'us-exteriors', color: '#2D5F2D', accent: 'forest' },
            us_development: { name: 'US Development', slug: 'us-development', color: '#C4AF94', accent: 'tan' },
        },

        // Navigation items
        navItems: [
            { page: 'home', hash: '#home', label: 'Dashboard', icon: 'layout-dashboard' },
            { page: 'calendar', hash: '#calendar', label: 'Calendar', icon: 'calendar' },
            { page: 'content', hash: '#content', label: 'Content Library', icon: 'file-text' },
            { page: 'reactivation', hash: '#reactivation', label: 'Reactivation', icon: 'users' },
            { page: 'settings', hash: '#settings', label: 'Settings', icon: 'settings' },
        ],

        // Page metadata
        pageMeta: {
            home: { title: 'Dashboard', subtitle: 'Overview of all marketing systems' },
            calendar: { title: 'LinkedIn Calendar', subtitle: 'Scheduled posts and events' },
            'post-detail': { title: 'Post Detail', subtitle: 'Review and manage post' },
            content: { title: 'Content Library', subtitle: 'Articles and content management' },
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
