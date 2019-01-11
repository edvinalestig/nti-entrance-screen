# coding: utf-8
from time import strftime
from flask import Flask, render_template
import vasttrafik

app = Flask(__name__)

with open("creds.txt") as f:
    key, secret = f.readlines()

vt = vasttrafik.Reseplaneraren(key.strip(), secret.strip(), 1)
chalmers_id = 9021014001960000
chalmers_tg_id = 9021014001970000
chalmersplatsen_id = 9021014001961000
kapellplatsen_id = 9021014003760000


def get_departures(stop):
    departures = vt.departureBoard(id=stop, date=strftime("%Y%m%d"), time=strftime("%H:%M"))
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
            print("Something has gone wrong")

        i = 0
        added = False
        while i < len(arr):
            # print(arr[i].get("sname") == dep.get("sname"), arr[i].get("direction") == dep.get("direction"))
            if arr[i].get("sname") == dep.get("sname") and arr[i].get("direction") == dep.get("direction"):
                added = True
                if len(arr[i].get("departures")) >= 2:
                    break
                else:
                    arr[i]["departures"].append(calculate_minutes(dep))
                    break
                    # print(arr[i]["departures"])
            i += 1

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
    print(arr)
    return sorted(arr, key=lambda dep: int(dep['sname']))


def calculate_minutes(departure):
    # Does not work when passing midnight
    d_time = departure.get("rtTime")
    if d_time == None:
        realtime = False
        d_time = departure.get("time")
    else:
        realtime = True

    hr, mn = d_time.split(":")
    mn = int(mn)
    mn += int(hr) * 60
    # Minutes since midnight

    # Now:
    n_mn = int(strftime("%M")) + int(strftime("%H")) * 60

    # Time left:
    countdown = mn - n_mn

    if realtime:
        if countdown == 0:
            return "Nu"
        else:
            return countdown
    else:
        return f'Ca {countdown}'


# ------- ROUTES --------

@app.route("/")
def index():
    cdep = format_departures(get_departures(chalmers_id))
    ctgdep = format_departures(get_departures(chalmers_tg_id))
    cpdep = format_departures(get_departures(chalmersplatsen_id))
    kdep = format_departures(get_departures(kapellplatsen_id))
    stops = (("Chalmers", cdep), ("Kapellplatsen", kdep), ("Chalmers Tvärgata", ctgdep), ("Chalmersplatsen", cpdep))
    print("--------------\n", stops, "\n--------------\n")

    return render_template("template.jinja", stops=stops)