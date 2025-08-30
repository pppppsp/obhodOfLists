const canvas = document.getElementById("signature_canvas");
const context = canvas.getContext("2d");
let drawing = false;
localStorage.clear()
canvas.addEventListener("mousedown", (e) => {
    drawing = true;
    context.beginPath();
    context.moveTo(e.offsetX, e.offsetY);
});

canvas.addEventListener("mousemove", (e) => {
    if (drawing) {
        context.lineTo(e.offsetX, e.offsetY);
        context.stroke();
    }
});

canvas.addEventListener("mouseup", () => {
    drawing = false;
});

// Очистка канваса
document.getElementById("clear_button").addEventListener("click", () => {
    context.clearRect(0, 0, canvas.width, canvas.height);
});

// Сохранение подписи в скрытое поле
document.getElementById("signature-form").addEventListener("submit", function(event) {
    event.preventDefault();  // Останавливаем стандартное поведение отправки формы

    console.log("Форма отправляется");

    // Получаем данные из канваса
    const canvas = document.getElementById("signature_canvas");
    const signatureData = canvas.toDataURL("image/png");
    console.log("Подпись в формате base64:", signatureData);

    if (!signatureData || signatureData === "data:image/png;base64,") {
        alert("Пожалуйста, нарисуйте подпись перед отправкой формы.");
    } else {
        // Записываем данные подписи в скрытое поле
        document.getElementById("signature_data").value = signatureData;

        // После обработки данных, отправляем форму вручную
        this.submit();  // Отправляем форму вручную
    }
});
