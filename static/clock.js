const clockElement = document.getElementById("clock");

function updateClock() {
    clockElement.innerHTML = new Date().toTimeString().split(" ")[0];
    setTimeout(updateClock, 1000);
}

updateClock();
setTimeout(() => document.location.reload(true), 15000);