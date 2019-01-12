const clockElement = document.getElementById("clock");
let data;

function updateClock() {
    clockElement.innerHTML = new Date().toTimeString().split(" ")[0];
    setTimeout(updateClock, 1000);
}

updateClock();
getJson();

function getJson() {
    let req = new XMLHttpRequest();
    req.addEventListener("load", updateScreen);
    req.open("GET", "/getinfo");
    req.send();
}

function updateScreen() {
    data = JSON.parse(this.responseText);
    console.log(data);
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
    
    printDisruption(data);
    printDepartures("chalmers", data.chalmers);
    printDepartures("chalmerstg", data.chalmerstg);
    printDepartures("chalmersplatsen", data.chalmersplatsen);
    printDepartures("kapellplatsen", data.kapellplatsen);

    setTimeout(getJson, 15000);
}

function printDisruption(data) {
    const disdiv = document.getElementById("disruptions");
    if (data.disruptions) {
        const h2 = document.createElement("h2");
        h2.innerHTML = data.disruptions[0];
        const h4 = document.createElement("h4");
        h4.innerHTML = data.disruptions[1]
        disdiv.appendChild(h2);
        disdiv.appendChild(h4);
    } else {
        const h1 = document.createElement("h1");
        h1.innerHTML = "Inga trafikstörningar!";
        disdiv.appendChild(h1);
    }
}

function printDepartures(name, departures) {
    const table = document.getElementById(name + "table");
    if (typeof departures == "string") {
        const row = document.createElement("tr");
        table.appendChild(row);
        row.innerHTML = departures;
    } else {
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