const infoBox = document.querySelector('[class="event-details"]');
const closeBtn = document.querySelector('[class="event-details"] button.close');

const events = document.querySelectorAll('.event');

const nameField = document.querySelector('[data-name="name"]');
const datesField = document.querySelector('[data-name="dates"]');
const timeField = document.querySelector('[data-name="time"]');
const placeField = document.querySelector('[data-name="place"]');
const teachersField = document.querySelector('[data-name="teachers"]');
const peopleField = document.querySelector('[data-name="people"]');
const linkField = infoBox.querySelector('a.reg-info');

const filtersMenu = document.querySelector('.event-filters');
const eventFilters = document.querySelectorAll('.event-filters input[type="checkbox"]');


for (let event of events) {
    event.addEventListener("click", showInfoBox);
}

closeBtn.addEventListener("click", () => {
    infoBox.close();
})

function showInfoBox(e) {
    const btn = e.target;

    nameField.innerText = btn.dataset.name;
    datesField.innerText = btn.dataset.dates;
    timeField.innerText = btn.dataset.time || "";
    placeField.innerText = btn.dataset.place;
    teachersField.innerText = btn.dataset.teachers;
    peopleField.innerText = btn.dataset.people;
    linkField.href = btn.dataset.link;

    timeField.closest("tr").hidden = !btn.dataset.time;
    teachersField.closest("tr").hidden = !btn.dataset.teachers;
    peopleField.closest("tr").hidden = !btn.dataset.people;
    linkField.style.display = !btn.dataset.link ? 'none': 'block';

    infoBox.showModal();
}


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
	const saved = localStorage.getItem(checkbox.id);
	if (saved !== null) {
	    checkbox.checked = saved === '1';
	}
    }
}

function updateMask() {
  const { scrollLeft, scrollWidth, clientWidth } = filtersMenu;
  const maxScroll = scrollWidth - clientWidth;
  const fade = '4ch';

  filtersMenu.style.setProperty(
    '--fade-left',
    scrollLeft > 0 ? `${fade}` : '0px'
  );

  filtersMenu.style.setProperty(
    '--fade-right',
    scrollLeft < maxScroll - 1 ? `${fade}` : '0px'
  );
}

loadFiltersState();
applyAllFilters();

filtersMenu.addEventListener('scroll', updateMask);
window.addEventListener('resize', updateMask);
updateMask();
