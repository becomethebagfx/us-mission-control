/**
 * Mission Control — Calendar Page
 * Renders a FullCalendar instance into #page-calendar with
 * company-colored events and click-to-navigate for posts.
 */
window.PageCalendar = {
    _calendar: null,

    async render(company) {
        const container = document.getElementById('page-calendar');
        if (!container) return;

        // Destroy previous calendar instance to prevent duplicates
        if (this._calendar) {
            this._calendar.destroy();
            this._calendar = null;
        }

        // Show loading state
        container.innerHTML = `
            <div class="flex items-center justify-center py-20">
                <div class="mc-spinner"></div>
                <span class="ml-3 text-sm text-gray-500">Loading calendar...</span>
            </div>`;

        try {
            // Fetch events from API
            const events = await API.calendar.events(company);

            // Prepare container — FullCalendar needs an empty div
            container.innerHTML = '<div id="fc-container" style="min-height: 600px;"></div>';

            this._initCalendar(events || []);
        } catch (err) {
            console.error('PageCalendar.render error:', err);
            container.innerHTML = `
                <div class="mc-card">
                    <div class="mc-card-body text-center py-12">
                        <i data-lucide="alert-triangle" class="w-8 h-8 text-red-400 mx-auto mb-3"></i>
                        <p class="text-sm text-gray-600">Failed to load calendar events.</p>
                        <p class="text-xs text-gray-400 mt-1">${this._esc(err.message)}</p>
                    </div>
                </div>`;
            if (window.lucide) lucide.createIcons();
        }
    },

    /* ------------------------------------------------------------------ */
    /*  FullCalendar Initialization                                        */
    /* ------------------------------------------------------------------ */

    _initCalendar(rawEvents) {
        const calendarEl = document.getElementById('fc-container');
        if (!calendarEl) return;

        // Company color map for fallback when event has no color
        const companyColors = {
            'us-framing': '#4A90D9',
            'us-drywall': '#B8860B',
            'us-exteriors': '#2D5F2D',
            'us-development': '#C4AF94',
        };

        // Map API events into FullCalendar event objects
        const events = rawEvents.map(ev => ({
            id: String(ev.id),
            title: ev.title || 'Untitled',
            start: ev.start,
            end: ev.end || null,
            backgroundColor: ev.color || companyColors[ev.company_slug] || '#4A90D9',
            borderColor: ev.color || companyColors[ev.company_slug] || '#4A90D9',
            textColor: '#ffffff',
            extendedProps: {
                company: ev.company || '',
                company_slug: ev.company_slug || '',
                type: ev.type || '',
                originalId: ev.id,
            },
        }));

        this._calendar = new FullCalendar.Calendar(calendarEl, {
            // Views
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay',
            },
            buttonText: {
                today: 'Today',
                month: 'Month',
                week: 'Week',
                day: 'Day',
            },

            // Appearance
            height: 'auto',
            dayMaxEvents: 3,
            nowIndicator: true,
            firstDay: 0, // Sunday

            // Events
            events: events,

            // Click handler — navigate to post detail for post events
            eventClick: function(info) {
                const props = info.event.extendedProps || {};
                if (props.type === 'post') {
                    // Extract post ID from event id (may be prefixed, e.g. "post-123")
                    const eventId = info.event.id;
                    const postId = eventId.replace(/^post-/, '');
                    window.location.hash = '#post-detail/' + postId;
                }
            },

            // Tooltip on hover via native title attribute
            eventDidMount: function(info) {
                const props = info.event.extendedProps || {};
                const parts = [info.event.title];
                if (props.company) parts.push(props.company);
                if (props.type) parts.push('Type: ' + props.type);
                info.el.setAttribute('title', parts.join(' \u2014 '));
            },
        });

        this._calendar.render();
    },

    /* ------------------------------------------------------------------ */
    /*  Helpers                                                            */
    /* ------------------------------------------------------------------ */

    _esc(str) {
        if (str == null) return '';
        const d = document.createElement('div');
        d.textContent = String(str);
        return d.innerHTML;
    },
};
