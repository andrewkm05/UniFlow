const addBtn = document.getElementById('add-btn');
const clearBtn = document.getElementById('clear-btn');
const formWrap = document.getElementById('form-wrap');
const fDay = document.getElementById('f-day');
const fStart = document.getElementById('f-start');
const fEnd = document.getElementById('f-end');
const fTitle = document.getElementById('f-title');
const saveItem = document.getElementById('save-item');
const cancelItem = document.getElementById('cancel-item');
const weekLists = document.querySelectorAll('.day-list');

// Restore data (local storage)
let schedule = JSON.parse(localStorage.getItem('schedule')) || {
    days: {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
};

// Render function
function renderSchedule() {
    weekLists.forEach(list => list.innerHTML = '');

    // for each day (0-6)
    for (let day in schedule.days){
        const entries = schedule.days[day];

        // sort by time
        entries.sort((a, b) => a.start.localeCompare(b.start));

        // creating list's data
        entries.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = "list-group-item d-flex justify-content-between align-items-center";

            // Text: title, time and delete button (x)
            li.innerHTML = `
            <span>
                <strong>${item.title}</strong> <br>${item.start}-${item.end}
            </span>
            <button class="btn btn-sm delete-btn" style="border: none;" data-day="${day}" data-index="${index}">
                x  
            </button>
            `;

            weekLists[day].appendChild(li);
        });
    }

    // Activate delete button (x)
    document.querySelectorAll('.delete-btn').forEach(btn =>{
        btn.addEventListener('click', (e) => {
            const d = e.target.getAttribute('data-day');
            const i = e.target.getAttribute('data-index');
            
            if (confirm("Delete this event?")){
                schedule.days[d].splice(i, 1);
                saveToStorage();
                renderSchedule();
            }
        });
    });
}

// Save function
function saveToStorage() {
    localStorage.setItem('schedule', JSON.stringify(schedule));
}

// Add new item function
if(saveItem) {
    saveItem.addEventListener("click", () => {
        const day = fDay.value;
        const start = fStart.value;
        const end = fEnd.value;
        const title = fTitle.value.trim();

        if(!title || !start || !end)
            return alert("Please fill all fields!");
        
        schedule.days[day].push({ start, end, title });
        saveToStorage();
        renderSchedule();

        formWrap.classList.add("d-none");
    });
}

// Clear table function
if(clearBtn) {
    clearBtn.addEventListener("click", () => {
        if (confirm("Clear all schedule items?")){
            schedule = { days: {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []} };
            saveToStorage();
            renderSchedule();
        }
    });
}

// View/Hide form
if(addBtn) {
    addBtn.addEventListener("click", () => {
        formWrap.classList.remove("d-none");
        fTitle.value = "";
        fStart.value = "14:00";
        fEnd.value = "15:20";
        fDay.value = "0";
        fTitle.focus();
    });
}

if(cancelItem) {
    cancelItem.addEventListener("click", () => {
        formWrap.classList.add("d-none");
    });
}

renderSchedule();
