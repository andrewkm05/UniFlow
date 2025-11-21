// Main JS for Weekly Schedule modal and visual placement of slots on the time grid
// Used ChatGPT to learn about interactive time grid placement and how to turn time strings into minutes and then into grid rows (implementation is my own)
document.addEventListener('DOMContentLoaded', () => {
    const modalEl = document.getElementById('scheduleModal');

    // If no modal, nothing to do
    if(!modalEl)
        return;

    const modal = new bootstrap.Modal(modalEl);
    const form = document.getElementById('scheduleForm');
    const fId = document.getElementById('f-id');
    const fDay = document.getElementById('f-day');
    const fStart = document.getElementById('f-start');
    const fEnd = document.getElementById('f-end');
    const fTitle = document.getElementById('f-title');
    const fNotes = document.getElementById('f-notes');
    const titleEl = document.getElementById('scheduleModalLabel');

    // When modal is shown, decide whether it's for creating or editing a slot and populate the form fields accordingly using data attributes (lerarned from ChatGPT, implementation is my own)
    modalEl.addEventListener('show.bs.modal', (ev) => {
        const btn = ev.relatedTarget;
        const mode = btn?.dataset.mode || 'create';
        const weekday = btn?.dataset.weekday;

        // Reset form state everytime modal is shown
        form.reset();
        fId.value = '';
        titleEl.textContent = mode === 'edit' ? 'Edit slot' : 'Add slot';

        // Preselect day if passed via button
        if(weekday != null)
            fDay.value = String(weekday);

        if(mode === 'create') {

            // Default values for a new slot
            const weekday = btn?.dataset.weekday;

            if(weekday != null)
                fDay.value = String(weekday);

            fStart.value = '09:00';
            fEnd.value = '10:00';
            fTitle.value = '';
            fNotes.value = '';
        }

        if(mode === 'edit') {

            // Fill the form with existing slot data
            fId.value = btn.dataset.id;
            fDay.value = btn.dataset.weekday;
            fStart.value = btn.dataset.start;
            fEnd.value = btn.dataset.end;
            fTitle.value = btn.dataset.title;
            fNotes.value = btn.dataset.notes;
        }
    });

    // Wire up all edit buttons to open the modal in edit mode 
    document.querySelectorAll('[data-mode="edit"]').forEach(btn => {
        btn.addEventListener('click', () => {
        
            modal.show();
        });
    });

    // TIME BASED SLOT PLACEMENT ON GRID
    // Immediately-invoked function to place all slots in the correct grid rows based on their start/end times
    (function placeSlot() {
        const SLOT_MIN = 30;    // Each slot is 30 minutes
        const START_MIN = 480;  // 08:00 in minutes (8*60 = 480 mins from midnight)
        const END_MIN = 1320;   // 22:00 in minutes (22*60 = 1320 mins from midnight)

        // Convert "HH:MM" string to minutes from midnight
        function toMins(hhmm){
            const [h, m] = hhmm.split(':').map(Number);
            return h*60 + m;
        }

        // For each slot element, compute its gridRow based on start/end time
        document.querySelectorAll('.day-list .slot').forEach(li => {
            const s = li.getAttribute('data-start');
            const e = li.getAttribute('data-end');

            if(!s || !e)
                return;

            let start = toMins(s);
            let end = toMins(e);

            // Clamp to schedule range [START_MIN, END_MIN]
            start = Math.max(start, START_MIN);
            end = Math.min(end, END_MIN);

            if(end <= start)
                return;

            // Convert minutes to grid rows +1 because grid rows start at 1
            const rowStart = Math.floor((start - START_MIN) / SLOT_MIN) + 1;
            const rowEnd = Math.ceil((end - START_MIN) / SLOT_MIN) + 1;

            li.style.gridRow = `${rowStart} / ${rowEnd}`;
        });
    })();
    
});