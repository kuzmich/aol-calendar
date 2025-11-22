const addBox = document.querySelector(".add-event");
const editBox = document.querySelector(".edit-event");
const addBtn = document.querySelector(".add-event-btn");
const events = document.querySelectorAll('.event');

addBtn.addEventListener("click", (e) => {
    addBox.showModal();
})

for (let event of events) {
    event.addEventListener("click", loadEditEventForm)
}


async function loadEditEventForm(e) {
    const btn = e.target;
    const eventId = btn.dataset.id;
    // запросим форму редактирования по id события
    let resp = await fetch(`/event/form/${eventId}`);
    if (resp.ok) { // если HTTP-статус в диапазоне 200-299
	let formHtml = await resp.text();
	editBox.innerHTML = formHtml;
	editBox.querySelector("form").addEventListener("submit", submitDialogForm);
	editBox.showModal();
    } else {
	alert("Ошибка HTTP: " + resp.status);
    }
}


async function submitDialogForm(e) {
    e.preventDefault();

    const form = e.target;
    const url = form.action;
    const dialog = form.closest("dialog");

    // Отправляем форму через fetch
    const response = await fetch(url, {
        method: "POST",
        body: new FormData(form),
    });

    // Получаем HTML с сервера
    const html = await response.text();

    // Если сервер вернул новую форму (например, с ошибками)
    if (!response.ok || html.includes("form-error")) {
	// Заменяем содержимое диалога новой формой
	dialog.innerHTML = html;
	// Повторно навешиваем обработчик, т.к. форма пересоздалась
	dialog.querySelector("form").addEventListener("submit", arguments.callee);
	return;
    }

    if (response.redirected) {
	// Если сервер вернул редирект - закрываем диалог
	dialog.close();
	// и обновляем календарь
	month = parseInt(form.querySelector('[name="start-date"]').value.split('-')[1]);
	window.location.href = response.url + `#${month}`;
	return;
    }
}
