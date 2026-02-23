/**
 * Mission Control — API Client
 * Fetch wrapper with error handling and base URL configuration.
 */
const API = {
    baseURL: '/api',

    async get(path, params = {}) {
        const url = new URL(this.baseURL + path, window.location.origin);
        Object.entries(params).forEach(([k, v]) => {
            if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v);
        });
        const res = await fetch(url.toString());
        if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
        return res.json();
    },

    async post(path, body = {}) {
        const res = await fetch(this.baseURL + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
        return res.json();
    },

    async put(path, body = {}) {
        const res = await fetch(this.baseURL + path, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
        return res.json();
    },

    // Convenience methods
    dashboard: {
        summary: (company) => API.get('/dashboard/summary', { company }),
    },
    calendar: {
        events: (company) => API.get('/calendar/events', { company }),
    },
    posts: {
        list: (company, status) => API.get('/posts/', { company, status }),
        stats: (company) => API.get('/posts/stats', { company }),
        get: (id) => API.get(`/posts/${id}`),
        update: (id, data) => API.put(`/posts/${id}`, data),
        approve: (id) => API.post(`/posts/${id}/approve`),
        reject: (id) => API.post(`/posts/${id}/reject`),
        reschedule: (id, date) => API.post(`/posts/${id}/reschedule`, { scheduled_date: date }),
    },
    content: {
        list: (company, status) => API.get('/content/', { company, status }),
        stats: (company) => API.get('/content/stats', { company }),
        topics: () => API.get('/content/topics'),
        get: (id) => API.get(`/content/${id}`),
        approve: (id) => API.post(`/content/${id}/approve`),
        publish: (id) => API.post(`/content/${id}/publish`),
    },
    reactivation: {
        leads: (company, status) => API.get('/reactivation/leads', { company, status }),
        lead: (id) => API.get(`/reactivation/leads/${id}`),
        funnel: (company) => API.get('/reactivation/funnel', { company }),
        metrics: (company) => API.get('/reactivation/metrics', { company }),
        sequences: () => API.get('/reactivation/sequences'),
    },
    settings: {
        tokens: () => API.get('/settings/tokens'),
        companies: () => API.get('/settings/companies'),
        company: (slug) => API.get(`/settings/companies/${slug}`),
        system: () => API.get('/settings/system'),
    },
    gbp: {
        locations: () => API.get('/gbp/locations'),
        insights: () => API.get('/gbp/insights'),
    },
    aeo: {
        queries: () => API.get('/aeo/queries'),
        stats: () => API.get('/aeo/stats'),
    },
    reviews: {
        list: () => API.get('/reviews/'),
        summary: () => API.get('/reviews/summary'),
        reply: (id, text) => API.post(`/reviews/${id}/reply`, { reply: text }),
    },
    brandAudit: {
        list: () => API.get('/brand-audit/'),
        summary: () => API.get('/brand-audit/summary'),
    },
    assets: {
        list: (company) => API.get('/assets/', { company }),
        stats: () => API.get('/assets/stats'),
    },
    quality: {
        runs: (company, contentType, status) => API.get('/quality/runs', { company, content_type: contentType, status }),
        run: (id) => API.get(`/quality/runs/${id}`),
        stats: (company) => API.get('/quality/stats', { company }),
        contentTypes: () => API.get('/quality/content-types'),
    },
    builder: {
        chat: (sessionId, message, siteSite) => API.post('/builder/chat', { session_id: sessionId, message, site_slug: siteSite }),
        sessions: () => API.get('/builder/sessions'),
        session: (id) => API.get(`/builder/sessions/${id}`),
        sites: () => API.get('/builder/sites'),
        preview: (sessionId) => API.post('/builder/preview', { session_id: sessionId }),
        deploy: (sessionId, branchName) => API.post('/builder/deploy', { session_id: sessionId, branch_name: branchName }),
        discard: (sessionId, branchName) => API.post('/builder/discard', { session_id: sessionId, branch_name: branchName }),
        rollback: (siteSite, sha) => API.post('/builder/rollback', { site_slug: siteSite, commit_sha: sha }),
        deploys: (siteSite) => API.get('/builder/deploys', { site_slug: siteSite }),
        usage: () => API.get('/builder/usage'),
    },
    monitoring: {
        deploys: (site, range) => API.get('/monitoring/deploys', { site, range }),
        deploy: (id, site) => API.get(`/monitoring/deploy/${id}`, { site }),
        performance: (site) => API.get('/monitoring/performance', { site }),
        logs: (site, level, range) => API.get('/monitoring/logs', { site, level, range }),
        metrics: (site, range) => API.get('/monitoring/metrics', { site, range }),
    },
    brief: {
        latest: () => API.get('/brief/latest'),
        history: (limit) => API.get('/brief/history', { limit }),
        generate: () => API.post('/brief/generate'),
        config: () => API.get('/brief/config'),
        updateConfig: (data) => API.put('/brief/config', data),
    },
};
