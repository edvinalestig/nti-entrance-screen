# coding: utf-8
import json
from time import strftime
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template
import vasttrafik

app = Flask(__name__)

# Update every 10 minutes
# Return list of tuples
def get_disruptions():
    if situation["updated"] < datetime.now() - timedelta(minutes=10):
        situation["updated"] = datetime.now()
        situation["situations"] = get_trafficsituation()
    if len(situation["situations"]) > 0:
        # Cycle thourough the disruptions if there are more than one
        situation["previous_shown"] = (situation["previous_shown"] + 1) % len(situation["situations"])
        return situation["situations"][ situation["previous_shown"]]
    else:
        return None

# Get the lastest disruptions from västtrafik
def get_trafficsituation():
    print("Updating disruptions")
    arr = []
    traffic = ts.trafficsituations()
    for situation in traffic:
        # Skip disruptions which aren't classed as 'severe'
        if situation.get("severity") != "severe":
            continue
        for stop in situation.get("affectedStopPoints"):
            name = stop.get("name")
            # Get only disruptions concerning the nearby stops
            if name == "Chalmers" or name == "Kapellplatsen" or name == "Chalmers Tvärgata" or name == "Chalmersplatsen":
                # Skip night-only disruptions
                if not "nattetid" in situation.get("description").lower():
                    arr.append(situation)

    outarr = []
    for situation in arr:
        # Get the start time and current time
        timeformat = "%Y-%m-%dT%H%M%S%z" # Format from västtrafik
        time = situation.get("startTime").replace(":", "")
        time = datetime.strptime(time, timeformat)
        now = datetime.now(timezone.utc)
        # Add it to the output array only if the disruption has started
        if time <= now:
            relevant = (situation.get("title"), situation.get("description"))
            # Skip duplicates
            if relevant not in outarr:
                outarr.append(relevant)

    return outarr

# Get 2 departures per line and destination within 1 hour
def get_departures(stop):
    departures = vt.departureBoard(id=stop, date=strftime("%Y%m%d"), time=strftime("%H:%M"), timeSpan=60, maxDeparturesPerLine=2)
    return departures.get("DepartureBoard").get("Departure")


def format_departures(departures):
    if departures == None:
        return "Inga avgångar hittade!"

    # Information needed:
    # Line nr
    # Destination
    # Minutes until departures 1 and 2
    # Colours
    # Sorted by line number
    arr = []

    for dep in departures:
        if len(arr) == 0:
            arr.append({
                "sname": dep.get("sname"),
                "direction": dep.get("direction"),
                "departures": [calculate_minutes(dep)],
                "fgColor": dep.get("fgColor"),
                "bgColor": dep.get("bgColor")
            })
            continue

        i = 0
        added = False
        while i < len(arr):
            # Check if one similar departure is in the list
            # Add the second departure time to the departure dict
            if arr[i].get("sname") == dep.get("sname") and arr[i].get("direction") == dep.get("direction"):
                added = True
                if len(arr[i].get("departures")) >= 2:
                    break
                else:
                    arr[i]["departures"].append(calculate_minutes(dep))
                    break
                    # print(arr[i]["departures"])
            i += 1

        # No similar departure in the list
        # Add the relevant info to a dict
        if not added:
            arr.append({
                "sname": dep.get("sname"),
                "direction": dep.get("direction"),
                "departures": [calculate_minutes(dep)],
                "fgColor": dep.get("fgColor"),
                "bgColor": dep.get("bgColor")
            })
    return sort_departures(arr)


def sort_departures(arr):
    # Sort firstly by line number and secondly by destination
    sorted_by_destination = sorted(arr, key=lambda dep: dep["direction"])
    sorted_by_line = sorted(sorted_by_destination, key=lambda dep: int(dep['sname']))
    return sorted_by_line


# Get minutes until departure
def calculate_minutes(departure):
    d_time = departure.get("rtTime")
    if d_time == None:
        realtime = False
        d_time = departure.get("time")
    else:
        realtime = True

    # Convert it all to minutes
    hour, minutes = d_time.split(":")
    minutes = int(minutes)
    minutes += int(hour) * 60
    # Minutes since midnight

    # Now:
    minutes_now = int(strftime("%M")) + int(strftime("%H")) * 60

    # Time left:
    countdown = minutes - minutes_now

    if countdown < -1300:
        # Past midnight, 24 hours = 1440 min
        countdown += 1440

    if realtime:
        if countdown <= 0:
            return "Nu"
        else:
            return countdown
    else:
        return f'Ca {countdown}'


# -------- INIT  --------
with open("creds.txt") as f:
    key, secret = f.readlines()

auth = vasttrafik.Auth(key.strip(), secret.strip(), 1)
vt = vasttrafik.Reseplaneraren(auth)
ts = vasttrafik.TrafficSituations(auth)

# Stop ids
chalmers_id = 9021014001960000
chalmers_tg_id = 9021014001970000
chalmersplatsen_id = 9021014001961000
kapellplatsen_id = 9021014003760000

# Traffic disruptions
situation = {
    "updated": datetime.now(),
    "previous_shown": 0,
    "situations": get_trafficsituation()
}

# ------- ROUTES --------

@app.route("/")
def index():
    cdep = format_departures(get_departures(chalmers_id))
    ctgdep = format_departures(get_departures(chalmers_tg_id))
    cpdep = format_departures(get_departures(chalmersplatsen_id))
    kdep = format_departures(get_departures(kapellplatsen_id))
    stops = (("Chalmers", cdep), ("Kapellplatsen", kdep), ("Chalmers Tvärgata", ctgdep), ("Chalmersplatsen", cpdep))
    disruptions = get_disruptions()

    return render_template("template.jinja", stops=stops, disruptions=disruptions)

@app.route("/norefresh")
def norefresh():
    with open("index.html") as f:
        site = f.read()
    return site

@app.route("/getinfo")
def getinfo():
    cdep = format_departures(get_departures(chalmers_id))
    ctgdep = format_departures(get_departures(chalmers_tg_id))
    cpdep = format_departures(get_departures(chalmersplatsen_id))
    kdep = format_departures(get_departures(kapellplatsen_id))
    disruptions = get_disruptions()

    d = {
        "disruptions": disruptions,
        "chalmers": cdep,
        "chalmerstg": ctgdep,
        "chalmersplatsen": cpdep,
        "kapellplatsen": kdep
    }

    return json.dumps(d)