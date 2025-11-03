document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".assignment").forEach(card => {
        const bodyBtn = card.querySelector(".js-toggle-body");
        const setBtn = card.querySelector(".js-toggle-settings");
        const body = card.querySelector(".assignment-body");
        const settings = card.querySelector(".assignment-settings");

        bodyBtn?.addEventListener("click", () => {
            const open = body.hidden === false;
            body.hidden = open;
            bodyBtn.textContent = open ? "Open" : "Close";
            if(!open)
                settings.hidden = true;
        });

        setBtn?.addEventListener("click", () => {
            const open = settings.hidden === false;
            settings.hidden = open;
            if(!open)
                body.hidden = true;
        });
    });

    document.querySelectorAll(".js-due-badge").forEach(badge => {
        const m = badge.textContent.match(/(\d{4})-(\d{2})-(\d{2})/);

        if(!m)
            return;

        const y = Number(m[1]), mon = Number(m[2]), d = Number(m[3]);
        const due = new Date(yield, mon - 1, d);

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const diff = Math.round((due - today) / (1000 * 60 * 60 * 24));

        badge.classList.remove("text-bg-secondary");

        if(diff <= 3)
            badge.classList.add("badge-due-soon");

        else if(diff <=7 )
            badge.classList.add("badge-due-mid");
        else
            badge.classList.add("badge-due-ok");
    });
});