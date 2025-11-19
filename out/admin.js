const editBox = document.querySelector(".add-event");
const addBtn = document.querySelector(".add-event-btn");
const events = document.querySelectorAll('.event');

addBtn.addEventListener("click", (e) => {
    editBox.showModal();
})

for (let event of events) {
    event.addEventListener("click", (e) => {
	const btn = e.target;
	editBox.showModal();
    })
}
