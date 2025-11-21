// Store/restore the open assignment panels across page reloads using sessionStorage
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

// Auto-resize a textarea to fit its content
function autoResizeTextarea(t) {
    t.style.height = "auto";
    t.style.height = (t.scrollHeight || t.offsetHeight) + "px";
}

// Main DOMContentLoaded handler. Sets up all assignment cards UI behavior
// Used ChatGPT specifically to improve structure of DOM event handling around toggling panels/learned about requestAnimationFrame (implementation is my own)
document.addEventListener("DOMContentLoaded", () => {

    const openSet = loadOpen();

    // Toggle open/close logic for each assignment card
    document.querySelectorAll(".assignment").forEach(card => {
        const id = card.dataset.assignmentId;

        const bodyBtn = card.querySelector(".js-toggle-body");
        const setBtn = card.querySelector(".js-toggle-settings");
        const body = card.querySelector(".assignment-body");
        const settings = card.querySelector(".assignment-settings");

        // Restore previously open state
        if(id && openSet.has(id)) {
            body.hidden = false;

            if(bodyBtn)
                bodyBtn.textContent = "Close"
            
            if(setBtn){
                setBtn.disabled = true;
                setBtn.classList.add("opacity-50");
                setBtn.classList.add("cursor-not-allowed");
            }

            settings.hidden = true;
        }

        // Open/Close the body panel
        bodyBtn?.addEventListener("click", () => {
            const open = body.hidden === false;
            body.hidden = open;
            bodyBtn.textContent = open ? "Open" : "Close";

            if(setBtn){
                const disableEdit = !open;
                setBtn.disabled = disableEdit;
                setBtn.classList.toggle("opacity-50", disableEdit);
                setBtn.classList.toggle("cursor-not-allowed", disableEdit);
                setBtn.title = disableEdit ? "Close the body to enable editing" : "";
            }

            // When opening, auto-resize all textareas and hide settings 
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

        // Toggle the settings panel
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

    // Highlight due-dates based on how soon they are
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

    // Auto-resize textareas
    document.querySelectorAll(".assignments-page textarea").forEach(t => {
        t.style.overflow = "hidden";
        t.style.resize = "none";

        t.addEventListener("input", () => autoResizeTextarea(t));

        if(t.offsetParent !== null)
                autoResizeTextarea(t);
    });

    // Auto-open settings panel if "open" param is in URL
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

