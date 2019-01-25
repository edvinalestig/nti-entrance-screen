const clockElement = document.getElementById("clock");
let updateTimer;

Date.prototype.getWeek = function() {
    let date = new Date(this.getTime());
    date.setHours(0, 0, 0, 0);
    // Thursday in current week decides the year.
    date.setDate(date.getDate() + 3 - (date.getDay() + 6) % 7);
    // January 4 is always in week 1.
    const week1 = new Date(date.getFullYear(), 0, 4);
    // Adjust to Thursday in week 1 and count number of weeks from date to week1.
    return 1 + Math.round(((date.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
}

function updateClock() {
    clockElement.innerHTML = new Date().toTimeString().split(" ")[0];
    setTimeout(updateClock, 500);
}

function updateDate() {
    console.log("hello");
    const time = new Date();
    const week = time.getWeek();
    const weekday = time.getDay();
    const day = time.getDay();
    const month = time.getMonth();
    const year = time.getFullYear();

    const days = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"];
    const months = ["Januari", "Februari", "Mars", "April", "Maj", "Juni", "Juli", "Augusti", "September", "Oktober", "November", "December"];
    
    document.getElementById("date").innerHTML = days[weekday-1] + " " + day + " " + months[month];
    document.getElementById("week").innerHTML = "Vecka " + week + " " + year;

    setTimeout(updateDate, 3600000);
}

// Workaround for ä not working in the html
// const tvar = document.getElementById("tvar");
// tvar.innerHTML = "Chalmers Tvärgata";
// const mdag = document.getElementById("mdag");
// mdag.innerHTML = "Måndag";

updateClock();
updateDate();
getJson();

function getJson() {
    let req = new XMLHttpRequest();
    req.timeout = 10000;
    // req.onload = () => updateScreen(this.responseText);
    req.ontimeout = () => {
        console.error("XHR timeout");
        clearTimeout(updateTimer);
        updateTimer = setTimeout(getJson, 5000);
    };
    req.onerror = () => {
        console.error("XHR error");
        clearTimeout(updateTimer);
        updateTimer = setTimeout(getJson, 15000);
    }

    req.addEventListener("load", updateScreen);
    // req.addEventListener("timeout", e => {
    //     console.error(e);
    //     clearTimeout(updateTimer);
    //     updateTimer = setTimeout(getJson, 5000);
    // });
    // req.addEventListener("error", e => {
    //     console.error(e);
    //     clearTimeout(updateTimer);
    //     updateTimer = setTimeout(getJson, 15000);
    // });
    req.open("GET", "/getinfo");
    req.send();
}

function updateScreen() {
    if (this.status != 200) {
        console.error("Not 200 OK")
        clearTimeout(updateTimer);
        updateTimer = setTimeout(getJson, 15000);
        return;
    }

    const data = JSON.parse(this.responseText);
    // Clear the departure tables
    const tables = document.getElementsByClassName("table");
    for (table of tables) {
        while (table.firstChild) {
            table.removeChild(table.firstChild);
        }
    }
    // Clear the disruption div
    const disruptiondiv = document.getElementById("disruptions");
    while (disruptiondiv.firstChild) {
        disruptiondiv.removeChild(disruptiondiv.firstChild);
    }
    
    printDisruption(data.disruptions);
    printDepartures("chalmers", data.chalmers);
    printDepartures("chalmerstg", data.chalmerstg);
    printDepartures("chalmersplatsen", data.chalmersplatsen);
    printDepartures("kapellplatsen", data.kapellplatsen);

    // Update in 15 seconds
    clearTimeout(updateTimer);
    updateTimer = setTimeout(getJson, 15000);
}

function printDisruption(data) {
    const disdiv = document.getElementById("disruptions");
    if (data) {
        // There is a disruption
        const h1 = document.createElement("h1");
        h1.innerHTML = data[0]; // Title
        const h3 = document.createElement("h3");
        h3.innerHTML = data[1] // Description
        disdiv.appendChild(h1);
        disdiv.appendChild(h3);
    } else {
        // There is not a disruption
        const h1 = document.createElement("h1");
        h1.innerHTML = "Inga trafikstörningar!";
        disdiv.appendChild(h1);
    }
}

function printDepartures(name, departures) {
    const table = document.getElementById(name + "table");
    if (typeof departures == "string") {
        // No departures found
        const row = document.createElement("tr");
        table.appendChild(row);
        row.innerHTML = departures;
        row.style = "text-align: center;"
    } else {
        
        if (!departures.length) {
            // Only one departure
            createElements(departures, table);
        } else {
            // Go through the departures and make a row for each
            for (dep of departures) {
                createElements(dep, table);
            }
        }
    }
}

function createElements(dep, table) {
    const row = document.createElement("tr");
    table.appendChild(row);
    // Line number
    const line = document.createElement("td");
    line.id = "line";
    line.style = "background-color: " + dep.fgColor + "; color: " + dep.bgColor + ";";
    line.innerHTML = dep.sname;
    row.appendChild(line);
    // Destination
    const dest = document.createElement("td");
    dest.classList.add("destination");
    dest.innerHTML = dep.direction;
    row.appendChild(dest);
    // Departures
    for (time of dep.departures) {
        const t = document.createElement("td");
        t.id = "dep";
        t.innerHTML = time;
        row.appendChild(t);
    }
}