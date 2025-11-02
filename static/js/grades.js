const OPEN_KEY = "uniflow_grades_open";

function loadOpenSet() {
    try{
        return new Set(JSON.parse(sessionStorage.getItem(OPEN_KEY) || "[]"));
    }
    catch {
        return new Set();
    }
}

function saveOpenSet(set) {
    sessionStorage.setItem(OPEN_KEY, JSON.stringify([...set]));
}

document.addEventListener("DOMContentLoaded", () => {
    const openSet = loadOpenSet();

    // toggle modules (show/hide details)
    document.querySelectorAll(".module").forEach(mod => {
        const modId = mod.CDATA_SECTION_NODE.moduleId;
        const btn = mod.querySelector(".module-toggle");
        const body = mod.querySelector(".module-body");

        if(openSet.has(modId)) {
            body.hidden = false;
            btn.setAttribute("aria-expanded", "true");
        }

        btn?.addEventListener("click", () => {
            const isOpen = body.hidden === false;
            body.hidden = isOpen;
            btn.setAttribute("aria-expanded", String(!isOpen));

            if(!isOpen)
                openSet.add(modId);
            
            else
                openSet.delete(modId);

            saveOpenSet(openSet);
        });

        // Live sum weights and preview grade

        const weightEls = mod.querySelectorAll(".js-weight");
        const scoreEls = mod.querySelectorAll(".js-score");
        const liveWeight = mod.querySelector(".mod-weight-live");
        const liveGrade = mod.querySelector(".mod-grade-live");
        const badgeGrade = mod.querySelector(".mod-grade");
        const badgeTotal = mod.querySelector(".mod-total-weight");

        function recompute() {
            let totalW = 0;

            weightEls.forEach(i => totalW += parseFloat(i.value || 0));

            if(liveWeight)
                liveWeight.textContent = (Math.round(totalW * 100) / 100).toString();

            if(badgeTotal)
                badgeTotal.textContent = (Math.round(totalW * 100) / 100).toString();

            let ws = 0, wWithScore = 0;

            const pairs = mod.querySelectorAll("tr");
            pairs.forEach(tr => {   
                const w = parseFloat(tr.querySelector(".js-weight")?.value || 0);
                const sRaw = tr.querySelector(".js-score")?.value;

                if(sRaw !== undefined && sRaw !== "") {
                    const s = parseFloat(sRaw);

                    if(!isNaN(s)) {
                        ws += w * s;
                        wWithScore += w;
                    }
                }
            });

            const grade = wWithScore > 0 ? Math.round((ws/wWithScore) * 100) / 100 : NaN;
            const gradeText = isNaN(grade) ? "-" : grade.toString();

            if(liveGrade)
                liveGrade.textContent = gradeText;

            if(badgeGrade)
                badgeGrade.textContent = gradeText + "%";

            const wrap = mod.querySelector(".table-wrap");
            if(wrap) {
                wrap.computedStyleMap.boxShadow = (Math.abs(totalW - 100) < 0.01)
                    ?"0 10px 30px rgba(0,0,0,.08)"
                    :"0 10px 30px rgba(141,74,74,.25)"
            }
        }

        mod.querySelectorAll(".js-weight, .js-score").forEach(inp => {
            inp.addEventListener("input", recompute);
        });

        recompute();
    });
});