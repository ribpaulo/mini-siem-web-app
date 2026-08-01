const dropzone = document.querySelector("#dropzone");
const fileInput = document.querySelector("#log_file");
const fileStatus = document.querySelector("#file-status");

const maximumSize = 2 * 1024 * 1024;
const allowedExtensions = [".log", ".txt"];

function showFile(file, assignToInput = false) {
    dropzone.classList.remove("is-dragging", "has-file", "is-error");

    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!allowedExtensions.includes(extension)) {
        fileInput.value = "";
        fileInput.setCustomValidity("Erlaubt sind nur .log- und .txt-Dateien.");
        fileStatus.textContent = "Nicht unterstützt: Bitte .log oder .txt verwenden.";
        dropzone.classList.add("is-error");
        return;
    }

    if (file.size > maximumSize) {
        fileInput.value = "";
        fileInput.setCustomValidity("Die Datei darf maximal 2 MB gross sein.");
        fileStatus.textContent = "Datei zu gross: maximal 2 MB erlaubt.";
        dropzone.classList.add("is-error");
        return;
    }

    if (assignToInput) {
        const transfer = new DataTransfer();
        transfer.items.add(file);
        fileInput.files = transfer.files;
    }

    fileInput.setCustomValidity("");
    fileStatus.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
    dropzone.classList.add("has-file");
}

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        showFile(fileInput.files[0]);
    }
});

["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropzone.classList.add("is-dragging");
    });
});

dropzone.addEventListener("dragleave", (event) => {
    event.preventDefault();
    if (!dropzone.contains(event.relatedTarget)) {
        dropzone.classList.remove("is-dragging");
    }
});

dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    event.stopPropagation();
    dropzone.classList.remove("is-dragging");

    if (event.dataTransfer.files.length !== 1) {
        fileInput.value = "";
        fileInput.setCustomValidity("Bitte genau eine Datei ablegen.");
        fileStatus.textContent = "Bitte genau eine Datei ablegen.";
        dropzone.classList.remove("has-file");
        dropzone.classList.add("is-error");
        return;
    }

    showFile(event.dataTransfer.files[0], true);
});
