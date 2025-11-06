const OPEN__TERMS_KEY = "uniflow_grades__terms_open";
const OPEN_MODULES_KEY = "uniflow_grades_modules_open"


function loadSet(key) {
    try{
        return new Set(JSON.parse(sessionStorage.getItem(key) || "[]"));
    }
    catch {
        return new Set();
    }
}

function saveSet(key, set) {
    sessionStorage.setItem(key, JSON.stringify([...set]));
}

document.addEventListener("DOMContentLoaded", () => {
    const openTerms = loadSet(OPEN__TERMS_KEY);
    const openModules = loadSet(OPEN_MODULES_KEY);

    // Terms toggle
    document.querySelectorAll(".term").forEach(termCard => {
        const termId = String(termCard.dataset.term);
        const header = termCard.querySelector(".term-header");
        const body = termCard.querySelector(".term-body");

        //restore
        if(openTerms.has(termId)){
            body.hidden = false;
            header.setAttribute("aria-expanded", "true");
        }

        header?.addEventListener("click", () => {
            const nowOpen = body.hidden;
            body.hidden = !nowOpen;

            header.setAttribute("aria-expanded", String(nowOpen));

            if(nowOpen)
                openTerms.add(termId);
            else
                openTerms.delete(termId);

            saveSet(OPEN__TERMS_KEY, openTerms);
        });
    });

    // Module toggle and live preview

    document.querySelectorAll(".module").forEach(mod => {
        const modId = String(mod.dataset.moduleId);
        const btn = mod.querySelector(".module-toggle");
        const body = mod.querySelector(".module-body");

        if(openModules.has(modId)) {
            body.hidden = false;
            btn.setAttribute("aria-expanded", "true");
        }

        btn?.addEventListener("click", () => {
            const isOpen = body.hidden === false;
            body.hidden = isOpen;
            btn.setAttribute("aria-expanded", String(!isOpen));

            if(!isOpen)
                openModules.add(modId);
            
            else
                openModules.delete(modId);

           saveSet(OPEN_MODULES_KEY, openModules);
        });

        // Live total and grade

        const liveWeight = mod.querySelector(".mod-weight-live");
        const liveGrade = mod.querySelector(".mod-grade-live");
        
        function recompute() {
            let totalW = 0;

            mod.querySelectorAll(".js-weight").forEach(i => totalW += parseFloat(i.value || 0));
            
            const twTxt = (Math.round(totalW * 100) /100).toString();

            if(liveWeight)
                liveWeight.textContent = twTxt;

            let ws = 0, wWithScore = 0;

            mod.querySelectorAll("tr").forEach(tr => {   
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
        }

        mod.querySelectorAll(".js-weight, .js-score").forEach(inp => {
            inp.addEventListener("input", recompute);
        });

        recompute();
    });
});