function paintDeadlines(scope = document) {

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    scope.querySelectorAll(".fld-close").forEach((inp) => {
        inp.classList.remove("deadline-soon", "deadline-passed");
        inp.title = "";

        if(!inp.value)
            return;
        
        const d = new Date(inp.value + "T00:00:00");

        if(isNaN(d))
            return;

        d.setHours(0, 0, 0, 0);
        const diffDays = Math.floor((d-today) / (1000 * 60 * 60 * 24));

        if(diffDays < 0) {
            inp.classList.add("deadline-passed");
            inp.title = `Closed ${Math.abs(diffDays)} day(s) ago`;
        }

        else if(diffDays <= 5) {
            inp.classList.add("deadline-soon");
            inp.title = `Closing soon (${diffDays} day${diffDays === 1 ? "" : "s"} left)`;
        }
    });
}
function autoDismissAlerts(delayMs = 2500) {
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach((el) => {
        if(el.hasAttribute("data-sticky"))
                return;
        
        setTimeout(() => {
            el.style.transition = "opacity .25s ease, transform .25s ease";
            el.style.opacity = "0";
            el.style.transform = "translateY(-4px)";

            setTimeout(() => el.remove(), 260);
            
        }, delayMs);
    });
}

function autosizeTextarea(el) {
    el.style.height = "auto";
    el.style.height = Math.max(46, el.scrollHeight) + "px";
}

function wireTextareaAutosize(scope = document) {
    scope.querySelectorAll("textarea").forEach((ta) => {
        autosizeTextarea(ta);
        ta.addEventListener("input", () => autosizeTextarea(ta));
    });
}

document.addEventListener("DOMContentLoaded", () => {

    const addBtn = document.getElementById("addRowBtn");
    const createRow = document.getElementById("createRow");

    if(addBtn && createRow) {
        addBtn.addEventListener("click", () => {

            if(createRow.style.display === "none" || createRow.style.display === "") {
                createRow.style.display = "table-row-group";

                const input = document.getElementById("create-company");

                if(input)
                    input.focus();
                else
                    createRow.style.display = "none";
                
                addBtn.disabled = true;
            }
        });
    }

    paintDeadlines();

    document.getElementById("appsBody")?.addEventListener("input", (e) => {
        if(e.target.matches(".fld-close"))
            paintDeadlines();
    });

    document.getElementById("appsBody")?.addEventListener("change", (e) => {
        if(e.target.matches(".fld-close"))
            paintDeadlines();
    });

    autoDismissAlerts(2500);

    wireTextareaAutosize();
});