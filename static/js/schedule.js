document.addEventListener('DOMContentLoaded', () => {
    const modalEl = document.getElementById('scheduleModal');

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

    modalEl.addEventListener('show.bs.modal', (ev) => {
        const btn = ev.relatedTarget;
        const mode = btn?.dataset.mode || 'create';
        const weekday = btn?.dataset.weekday;

        form.reset();
        fId.value = '';
        titleEl.textContent = mode === 'edit' ? 'Edit slot' : 'Add slot';

        if(weekday != null)
            fDay.value = String(weekday);

        if(mode === 'create') {
            const weekday = btn?.dataset.weekday;

            if(weekday != null)
                fDay.value = String(weekday);

            fStart.value = '09:00';
            fEnd.value = '10:00';
            fTitle.value = '';
            fNotes.value = '';
        }

        if(mode === 'edit') {
            fId.value = btn.dataset.id;
            fDay.value = btn.dataset.weekday;
            fStart.value = btn.dataset.start;
            fEnd.value = btn.dataset.end;
            fTitle.value = btn.dataset.title;
            fNotes.value = btn.dataset.notes;
        }
    });

    document.querySelectorAll('[data-mode="edit"]').forEach(btn => {
        btn.addEventListener('click', () => {
        
            modal.show();
        });
    });

    // Slot sizes change dynamicaly with the start-end time
    document.querySelectorAll('.slot').forEach(li => {
        const s = li.getAttribute('data-start');
        const e = li.getAttribute('data-end');

        if(!s || !e)
            return;

        const [sh, sm] = s.split(':').map(Number);
        const [eh, em] = e.split(':').map(Number);

        const startMin = sh*60 + sm;
        const endMin = eh*60 + em;

        let diffMin = Math.max(0, endMin - startMin);

        const spanHours = Math.max(1, diffMin / 60);

        li.style.setProperty('--slot-span', spanHours);
    });
});