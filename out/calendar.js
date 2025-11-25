const infoBox = document.querySelector('.event-details');
const closeBtn = document.querySelector('button.close');
const events = document.querySelectorAll('.event');
const nameField = document.querySelector('[data-name="name"]');
const datesField = document.querySelector('[data-name="dates"]');
const timeField = document.querySelector('[data-name="time"]');
const placeField = document.querySelector('[data-name="place"]');
const teachersField = document.querySelector('[data-name="teachers"]');
const peopleField = document.querySelector('[data-name="people"]');
const eventFilters = document.querySelectorAll('.event-filters input[type="checkbox"]');

for (let event of events) {
    event.addEventListener("click", (e) => {
	const btn = e.target;
	nameField.innerText = btn.dataset.name;
	datesField.innerText = btn.dataset.dates;
	timeField.innerText = btn.dataset.time || "";
	placeField.innerText = btn.dataset.place;
	teachersField.innerText = btn.dataset.teachers;
	peopleField.innerText = btn.dataset.people;

	infoBox.querySelectorAll("tr").forEach((tr) => {
	    tr.removeAttribute("hidden");
	})
	if (!btn.dataset.teachers) {
	    teachersField.closest("tr").setAttribute("hidden", true);
	}
	if (!btn.dataset.people) {
	    peopleField.closest("tr").setAttribute("hidden", true);
	}
	if (!btn.dataset.time) {
	    timeField.closest("tr").setAttribute("hidden", true);
	}

	infoBox.showModal();
    })
}

closeBtn.addEventListener("click", () => {
    infoBox.close();
})


// Фильтры по типам курсов
for (let checkbox of eventFilters) {
    checkbox.addEventListener("click", (e) => {
	const checkbox = e.target;
	applyFilter(checkbox);
	saveFilterState(checkbox);
    })
}

function applyFilter(checkbox) {
    const shouldShow = checkbox.checked;
    const targetTypes = checkbox.dataset.targetTypes.split(',');
    const allExcept = targetTypes[0].startsWith('!');

    if (allExcept) {
	targetTypes[0] = targetTypes[0].slice(1);
    }

    for (let event of events) {
	let isTargetType = targetTypes.some(cls => event.classList.contains(cls));
	if (!allExcept ? isTargetType : !isTargetType) {
	    event.style.display = shouldShow ? '': 'none';
	}
    }
}

function applyAllFilters() {
    for (let checkbox of eventFilters) {
	if (!checkbox.checked) {
	    applyFilter(checkbox);
	}
    }
}

function saveFilterState(checkbox) {
    localStorage.setItem(checkbox.id, checkbox.checked ? '1' : '0');
}

function loadFiltersState() {
    for (let checkbox of eventFilters) {
	const key = checkbox.id;
	const saved = localStorage.getItem(key);
	if (saved !== null) {
	    checkbox.checked = saved === '1';
	}
    }
}

loadFiltersState();
applyAllFilters();
