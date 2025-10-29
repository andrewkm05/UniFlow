// Local storage key where all rows been saved
const STORAGE_KEY = "uniflow_applies_v1";

// Lists with options for the "select" fields 
const STATUS_OPTIONS = [
    "Not Applied",
    "Interested",
    "Application Submitted",
    "Online Assessment",
    "Case Study",
    "HireVue",
    "Telephone Interview",
    "Video Interview",
    "Face-to-face Interview",
    "Assessment Centre",
    "Offer Received",
    "Rejected",
    "Not Interested"
];

const YESNO = ["Yes", "No", "Optional"];

// References to basic DOM elements
const bodyEl = document.getElementById("appliesBody");
const addBtn = document.getElementById("addRowBtn");

// Helpful Functions

// Its reading from the localStorage and it returns an array
function loadRows() {
    try{
        return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch{
        return [];
    }
}

// It writes the whole array icluding rows in localStorage
function saveRows(rows) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(rows));
}

// It creates a simple unique id for each row
function uid() {
    return Math.random().toString(36).slice(2, 10);
}

// Rendering:

// It produces <option>...</option> for a <select>
function optionList(arr, selected) {
    return arr
        .map(v => `<option ${v === selected ? "selected" : ""}>${v}</option>`)
        .join("");
}

// It creats a <tr> DOM row filled with inputs/selects
function renderRow(row) {
    const tr = document.createElement("tr");
    tr.dataset.id = row.id;

    tr.innerHTML = `
        <td>
            <select class="fld-status">
                ${optionList(STATUS_OPTIONS, row.status || "Not Applied")}
            </select>
        </td>

        <td>
            <input class="fld-company" type="text" placeholder="Company" value="${row.company || ""}">
        </td>

        <td>
            <input class="fld-prog" type="text" placeholder="Programme" value="${row.programme || ""}">
        </td>

        <td>
            <input class="fld-open" type="date" value="${row.opening || ""}">
        </td>

        <td>
            <input class="fld-close" type="date" value="${row.closing || ""}">
        </td>

        <td>
            <select class="fld-cv">
                ${optionList(YESNO, row.cv || "Yes")}
            </select>
        </td>

        <td>
            <select class="fld-cover">
                ${optionList(YESNO, row.cover || "Yes")}
            </select>
        </td>

        <td>
            <select class="fld-written">
                ${optionList(YESNO, row.written || "Yes")}
            </select>
        </td>

        <td>
            <textarea class="fld-notes" placeholder="Notes">${row.notes || ""}</textarea>
        </td>

        <td>
            <div class="row-actions">
                <button class="btn btn-sm btn-save rounded-pill px-3">Save</button>
                <button class="btn btn-sm btn-del rounded-pill px-3">x</button>
            </div>
        </td>
    `;

    bodyEl.appendChild(tr);
}

// It erases the <tbody> and re-make all the lines
function renderAll() {
    bodyEl.innerHTML = "";
    const rows = loadRows();
    rows.forEach(renderRow);
    checkDeadlines();
}

// Crud logic (add/save/delete):

// It colects the data from a <tr> and returns them as object
function collectRowData(tr) {
    return {
        id: tr.dataset.id || uid(),
        status: tr.querySelector(".fld-status").value(),
        company: tr.querySelector(".fld-company").value().trim(),
        programme: tr.querySelector(".fld-prog").value().trim(),
        opening: tr.querySelector(".fld-open").value(),
        closing: tr.querySelector(".fld-close").value(),
        cv: tr.querySelector(".fld-cv").value(),
        cover: tr.querySelector(".fld-cover").value(),
        written: tr.querySelector(".fld-written").value(),
        notes: tr.querySelector(".fld-notes").value().trim()
    };
}

// It creates an empty line at UI so the user can write and press the save button
function addEmptyRow() {
    const empty = {
        id: uid(),
        status: "Not Applied",
        company: "",
        programme: "",
        opening: "",
        closing: "",
        cv: "Yes",
        cover: "Yes",
        written: "Yes",
        notes: ""
    };

    renderRow(empty);

    document.querySelector(".table-wrap")?.scrollTo({ left: 99999, behavior: "smooth" });
}

// It takes the row's data, add them to the array and persist at localStorage
function saveRow(tr) {
    const rows = loadRows();
    const data = collectRowData(tr);

    const idx = rows.findIndex(x => x.id === data.id);
    if (idx >= 0)
            rows[idx] = data;
    
    saveRows(rows);
    checkDeadlines();
}

// It deletes a record from both localStorage and DOM
function deleteRow(tr) {
    const id = tr.dataset.id;
    const rows = loadRows().filter(x => x.id !== id);
    saveRows(rows);
    tr.remove();
}

// Highlight "closing date"

/**
 * It checks every "Closing Date" inputs and:
 * - If the date is passed -> .deadline-passed
 * - If the deadline is soon (<=5 days) -> .deadline-soon
 * - Else it clears the styles
 */
function checkDeadlines() {
    const today = new Date();

    document.querySelectorAll(".fld-close").forEach(input => {
        input.classList.remove("deadline-soon", "deadline-passed");

        if(!input.value)
            return;
        
        const close = new Date(input.value);
        
        const diffDays = Math.floor((close - today) / (1000 * 60 * 60 * 24));

        if(diffDays < 0) {
            input.classList.add("deadline-passed");
            input.title = `Closed ${Math.abs(diffDays)} day(s) ago`;
        }
        else if(diffDays <= 5) {
            input.classList.add("deadline-soon");
            input.title = `Closing soon (${diffDays} day${diffDays === 1 ? "" : "s"} left)`;
        }
        else {
            input.title = "";
        }
    });
}

// Conncecting the events:
document.addEventListener("DOMContentLoaded", () => {
    renderAll();

    addBtn?.addEventListener("click", addEmptyRow);

    bodyEl.addEventListener("click", (e) => {
        const tr = e.target.closest("tr");
        if(!tr)
            return;

        if(e.target.matches(".btn-save")) {
            saveRow(tr);
        }

        if(e.target.matches(".btn-del")) {
            if(confirm("Delete this entry?"))
                deleteRow();
        }
    });

    bodyEl.addEventListener("change", (e) => {
        if(e.target.matches(".fld-close"))
                checkDeadlines();
    });
});