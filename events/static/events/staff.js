// Ссылка «Редактировать» в окне события ведет на событие в Django-админке
const editLink = document.querySelector('[class="event-details"] a.edit-link');

for (let event of document.querySelectorAll('.event')) {
    event.addEventListener("click", (e) => {
	editLink.href = e.target.dataset.adminUrl;
    });
}
