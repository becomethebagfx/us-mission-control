/**
 * Mission Control — Calendar Page
 * Premium redesign: skeleton loading, card-wrapped calendar, breathing room.
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

        // Skeleton loading state
        container.innerHTML = `
            <div class="page-enter">
                <div class="skeleton" style="height:48px;border-radius:12px;margin-bottom:24px;max-width:320px"></div>
                <div class="mc-card">
                    <div class="mc-card-body">
                        <div class="skeleton" style="height:560px;border-radius:8px"></div>
                    </div>
                </div>
            </div>`;

        try {
            const events = await API.calendar.events(company);

            container.innerHTML = `
                <div class="page-enter">
                    <div class="mc-card">
                        <div class="mc-card-header">
                            <h3 class="flex items-center gap-2">
                                <i data-lucide="calendar" class="w-4 h-4 text-navy/60"></i>
                                LinkedIn Calendar
                            </h3>
                            <span class="text-xs text-gray-400">${(events || []).length} events</span>
                        </div>
                        <div class="mc-card-body">
                            <div id="fc-container" style="min-height: 600px;"></div>
                        </div>
                    </div>
                </div>`;

            this._initCalendar(events || []);
            if (window.lucide) lucide.createIcons();
        } catch (err) {
            console.error('PageCalendar.render error:', err);
            container.innerHTML = `
                <div class="page-enter">
                    <div class="mc-card">
                        <div class="empty-state">
                            <i data-lucide="calendar-x" class="empty-state-icon"></i>
                            <p class="empty-state-title">Failed to load calendar events</p>
                            <p class="empty-state-text">${this._esc(err.message)}</p>
                        </div>
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

        const companyColors = {
            'us-framing': '#4A90D9',
            'us-drywall': '#B8860B',
            'us-exteriors': '#2D5F2D',
            'us-development': '#C4AF94',
        };

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
            height: 'auto',
            dayMaxEvents: 3,
            nowIndicator: true,
            firstDay: 0,
            events: events,
            eventClick: function(info) {
                const props = info.event.extendedProps || {};
                if (props.type === 'post') {
                    const eventId = info.event.id;
                    const postId = eventId.replace(/^post-/, '');
                    window.location.hash = '#post-detail/' + postId;
                }
            },
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
