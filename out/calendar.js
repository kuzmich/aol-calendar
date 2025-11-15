const infoBox = document.querySelector('.event-details');
const closeBtn = document.querySelector('button.close');
const events = document.querySelectorAll('.event');
const nameField = document.querySelector('[data-name="name"]');
const datesField = document.querySelector('[data-name="dates"]');
const timeField = document.querySelector('[data-name="time"]');
const placeField = document.querySelector('[data-name="place"]');
const teachersField = document.querySelector('[data-name="teachers"]');
const peopleField = document.querySelector('[data-name="people"]');
const addBtn = document.querySelector(".add-event-btn");
const editBox = document.querySelector('.add-event');

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

if (addBtn) {
    addBtn.addEventListener("click", (e) => {
	editBox.showModal();
    })
}
