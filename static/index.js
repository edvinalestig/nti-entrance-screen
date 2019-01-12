const clockElement = document.getElementById("clock");

function updateClock() {
    clockElement.innerHTML = new Date().toTimeString().split(" ")[0];
    setTimeout(updateClock, 1000);
}

// Workaround for ä not working in the html
const tvar = document.getElementById("tvar");
tvar.innerHTML = "Chalmers Tvärgata";

updateClock();
getJson();

function getJson() {
    let req = new XMLHttpRequest();
    req.addEventListener("load", updateScreen);
    req.open("GET", "/getinfo");
    req.send();
}

function updateScreen() {
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
    setTimeout(getJson, 15000);
}

function printDisruption(data) {
    const disdiv = document.getElementById("disruptions");
    if (data) {
        // There is a disruption
        const h2 = document.createElement("h2");
        h2.innerHTML = data[0]; // Title
        const h4 = document.createElement("h4");
        h4.innerHTML = data[1] // Description
        disdiv.appendChild(h2);
        disdiv.appendChild(h4);
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
        // Go through the departures and make a row for each
        for (dep of departures) {
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
    }
}