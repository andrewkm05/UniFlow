// To keep assignments form open after any action until the user closes them
const OPEN_ASSIGNMENTS_KEY = "uniflow_assignments_open";

function loadOpen() {
    try{
        return new Set(JSON.parse(sessionStorage.getItem(OPEN_ASSIGNMENTS_KEY) || "[]"));
    }
    catch{
        return new Set();
    }
}

function saveOpen(set) {
    sessionStorage.setItem(OPEN_ASSIGNMENTS_KEY, JSON.stringify([...set]));
}

function autoResizeTextarea(t) {
    t.style.height = "auto";
    t.style.height = (t.scrollHeight || t.offsetHeight) + "px";
}


document.addEventListener("DOMContentLoaded", () => {

    const openSet = loadOpen();

    document.querySelectorAll(".assignment").forEach(card => {
        const id = card.dataset.assignmentId;

        const bodyBtn = card.querySelector(".js-toggle-body");
        const setBtn = card.querySelector(".js-toggle-settings");
        const body = card.querySelector(".assignment-body");
        const settings = card.querySelector(".assignment-settings");

        // reopen if it was open before refresh
        if(id && openSet.has(id)) {
            body.hidden = false;

            if(bodyBtn)
                bodyBtn.textContent = "Close"

            settings.hidden = true;
        }

        bodyBtn?.addEventListener("click", () => {
            const open = body.hidden === false;
            body.hidden = open;
            bodyBtn.textContent = open ? "Open" : "Close";
            if(!open){
                settings.hidden = true;

                requestAnimationFrame(() => {
                    card.querySelectorAll(".assignment-body textarea").forEach(autoResizeTextarea);
                });
                openSet.add(id);
            }                

            else
                openSet.delete(id)

            saveOpen(openSet);
        });

        setBtn?.addEventListener("click", () => {
            const open = settings.hidden === false;
            settings.hidden = open;
            if(!open){
                body.hidden = true;
                
                requestAnimationFrame(() => {
                    card.querySelectorAll(".assignment-settings textarea").forEach(autoResizeTextarea);
                });
                openSet.add(id);
            }
            else
                openSet.delete(id);

            saveOpen(openSet);                            
        });
    });

    document.querySelectorAll(".js-due-badge").forEach(badge => {
        const m = badge.textContent.match(/(\d{4})-(\d{2})-(\d{2})/);

        if(!m)
            return;

        const y = Number(m[1]), mon = Number(m[2]), d = Number(m[3]);
        const due = new Date(y, mon - 1, d);

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const diff = Math.round((due - today) / (1000 * 60 * 60 * 24));

        badge.classList.remove("text-bg-secondary", "badge-due-soon", "badge-due-mid", "badge-due-ok");

        if(diff <= 3)
            badge.classList.add("badge-due-soon");

        else if(diff <=7 )
            badge.classList.add("badge-due-mid");
        else
            badge.classList.add("badge-due-ok");
    });

    // Auto-expand notes textarea:

    document.querySelectorAll(".assignments-page textarea").forEach(t => {
        t.style.overflow = "hidden";
        t.style.resize = "none";

        t.addEventListener("input", () => autoResizeTextarea(t));

        if(t.offsetParent !== null)
                autoResizeTextarea(t);
    });

    // auto open settings when creating a new assignment
    const params = new URLSearchParams(location.search);
    const openId = params.get("open");

    if(openId){
        const card = document.querySelector(`.assignment[data-assignment-id="${openId}"]`);

        if(card){
            const body = card.querySelector(".assignment-body");
            const settings = card.querySelector(".assignment-settings");

            body.hidden = true;
            settings.hidden = false;

            history.replaceState({}, "", location.pathname);
        }
    }
});

