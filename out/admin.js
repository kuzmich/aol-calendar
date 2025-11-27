const addBox = document.querySelector(".add-event");
const editBox = document.querySelector(".edit-event");
const addBtn = document.querySelector(".add-event-btn");
let pressTimer;


addBox.querySelector("form").addEventListener("submit", submitDialogForm);

addBtn.addEventListener("click", (e) => {
    addBox.showModal();
})

for (let event of events) {
    event.removeEventListener("click", showInfoBox);
    event.addEventListener("click", chooseWhichBoxToShow);

    event.addEventListener('touchstart', longPressStart);
    event.addEventListener('touchend', longPressEnd);
}

function longPressStart(e) {
    pressTimer = setTimeout(
	() => showInfoBox(e),
	500
    );
}

function longPressEnd(e) {
    clearTimeout(pressTimer);
}

function chooseWhichBoxToShow(e) {
    if (e.altKey) {
	showInfoBox(e);
    } else {
	loadEditEventForm(e);
    }
}


async function loadEditEventForm(e) {
    const btn = e.target;
    const eventId = btn.dataset.id;

    // запросим форму редактирования по id события
    let resp = await fetch(getEditEventUrl(eventId));
    if (resp.ok) { // если HTTP-статус в диапазоне 200-299
	let formHtml = await resp.text();

	for (let form of editBox.querySelectorAll('form')) {
	    form.remove();
	}
	editBox.insertAdjacentHTML("beforeend", formHtml);

	let form = editBox.querySelector("form");
	form.addEventListener("submit", submitDialogForm);

	editBox.showModal();
    } else {
	alert("Ошибка HTTP: " + resp.status);
    }
}

async function submitDialogForm(e) {
    e.preventDefault();

    const btn = e.submitter;
    const form = e.target;
    const url = form.action;
    const dialog = form.closest("dialog");

    const formData = new FormData(form);

    // Добавляем информацию о том, какая кнопка была нажата
    if (btn && btn.name) {
        formData.append(btn.name, btn.value);
    }
    // Отправляем форму
    const response = await fetch(url, {
        method: "POST",
        body: formData,
    });

    // Получаем форму с сервера
    const formHtml = await response.text();

    // Если сервер вернул новую форму (например, с ошибками)
    if (!response.ok || formHtml.includes("error")) {
	// Заменяем содержимое диалога новой формой
	form.outerHTML = formHtml;
	// Повторно навешиваем обработчик, т.к. форма пересоздалась
	dialog.querySelector("form").addEventListener("submit", submitDialogForm);
	return;
    }

    if (response.redirected) {
	// Если сервер вернул редирект - закрываем диалог
	dialog.close();
	// и обновляем календарь
	let month = parseInt(form.querySelector('[name="start-date"]').value.split('-')[1]);
	let newUrl = response.url + `#${month}`;
	// обновляем страницу, даже если остаемся в том же месте календаря
	if (window.location.href === newUrl) {
	    window.location.reload()
	} else {
	    window.location.href = newUrl;
	}
	return;
    }
}
