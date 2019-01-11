function updateClock() {
    const clockElement = document.getElementById("clock");
    clockElement.innerHTML = new Date().toTimeString().split(" ")[0];
    setTimeout(updateClock, 1000);
}

updateClock();