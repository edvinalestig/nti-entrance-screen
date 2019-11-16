# coding: utf-8
import json
import requests
import os
from datetime import datetime, timezone, timedelta

from flask import Flask
import dateutil.tz as tz # Used for timezone stuff

import vasttrafik
import skolmaten
# import creds

app = Flask(__name__)

# Update every 5 minutes
# Return list of tuples
def get_disruptions():
    # Uses tz.gettz("Europe/Stockholm") to get Swedish time
    # The server is based in Ireland and uses the wrong time without it

    # Checks if 3 minutes have passed since the last update of disruptions
    if situation["updated"] < datetime.now(tz.gettz("Europe/Stockholm")) - timedelta(minutes=3):
        situation["updated"] = datetime.now(tz.gettz("Europe/Stockholm"))
        situation["situations"] = get_trafficsituation()

    out = {
        "updated": situation["updated"].strftime("%Y-%m-%d %H:%M:%S%z"),
        "situations": None
    }

    if len(situation["situations"]) > 0:
        # Cycle thourough the disruptions if there are more than one
        situation["previous_shown"] = (situation["previous_shown"] + 1) % len(situation["situations"])
        out["situations"] = situation["situations"][situation["previous_shown"]]

    return out


# Get the lastest disruptions from västtrafik
def get_trafficsituation():
    print("Updating disruptions")
    arr = []
    traffic = ts.trafficsituations()
    for situation in traffic:
        # Skip disruptions which aren't classed as 'severe' or 'normal'
        severity = situation.get("severity")
        if not (severity == "severe" or severity == "normal"):
            continue
        for stop in situation.get("affectedStopPoints"):
            name = stop.get("name")
            # Get only disruptions concerning the nearby stops
            if name == "Chalmers" or name == "Kapellplatsen" or name == "Chalmers Tvärgata" or name == "Chalmersplatsen":
                # Skip night-only disruptions
                if (not "nattetid" in situation.get("description").lower()) and (not "nattetid" in situation.get("title").lower()):
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
    time_now = datetime.now(tz.gettz("Europe/Stockholm"))
    date = time_now.strftime("%Y%m%d")
    time = time_now.strftime("%H:%M")

    departures = vt.departureBoard(id=stop, date=date, time=time, timeSpan=60, maxDeparturesPerLine=2)
    return departures.get("DepartureBoard").get("Departure")

# Get all stops at the same time
def get_async_departures(stops):
    time_now = datetime.now(tz.gettz("Europe/Stockholm"))
    date = time_now.strftime("%Y%m%d")
    time = time_now.strftime("%H:%M")

    departure_list = vt.asyncDepartureBoards(stops, date=date, time=time, timeSpan=60, maxDeparturesPerLine=2)
    output = []
    for dep in departure_list:
        output.append(dep.get("DepartureBoard").get("Departure"))

    return output


def format_departures(departures):
    if departures == None:
        return "Inga avgångar hittade!"
    if type(departures) == dict:
        # Only one departure
        print("hello")
        direction = departures.get("direction").split(" via ")[0].split(", ")[0]
        return ({
            "sname": departures.get("sname"),
            "direction": direction,
            "departures": [calculate_minutes(departures)],
            "fgColor": departures.get("fgColor"),
            "bgColor": departures.get("bgColor")
        })

    # Information needed:
    # Line nr
    # Destination
    # Minutes until departures 1 and 2
    # Colours
    # Sorted by line number
    arr = []
    # print(departures[0], departures[0].get("rtTime"), "\n")

    for dep in departures:
        direction = dep.get("direction").split(" via ")[0].split(", ")[0]
        if len(arr) == 0:
            # First departure has to be added manually
            # The loop doesn't work if there isn't anything in arr
            arr.append({
                "sname": dep.get("sname"),
                "direction": direction,
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
            if arr[i].get("sname") == dep.get("sname") and arr[i].get("direction") == direction:
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
                "direction": direction,
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
    if departure.get("cancelled"):
        return "Inställd"

    # Check if real time info is available
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
    time_now = datetime.now(tz.gettz("Europe/Stockholm"))
    minutes_now = int(time_now.strftime("%M")) + int(time_now.strftime("%H")) * 60

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

def get_temperature():
    if temp_situation["updated"] == 0 or temp_situation["updated"] < datetime.now(tz.gettz("Europe/Stockholm")) - timedelta(minutes=10):
        print("Updating temperatures")
        openweathermap_key = os.environ["OWM_KEY"].strip()
        api_call = "https://api.openweathermap.org/data/2.5/weather?q=Göteborg&APPID=" + openweathermap_key
        r = requests.get(api_call)
        r_json = json.loads(str(r.json()).replace("'", '"'))
        temp_now = str(round((r_json["main"]["temp"]-272.15), 1)) + "°C"
        wheater_now = getWeatherEmoji(r_json["weather"][0]["id"])

        hourly_call = "https://api.openweathermap.org/data/2.5/forecast?q=Göteborg&APPID=" + openweathermap_key
        hourly_r = requests.get(hourly_call)
        hourly_json = json.loads(str(hourly_r.json()).replace("'", '"'))
        temp0 = str(round((hourly_json["list"][0]["main"]["temp"]-272.15),1)) + "°C"
        temp0time = datetime.fromtimestamp(hourly_json["list"][0]["dt"], tz.gettz("Europe/Stockholm")).strftime('%H:%M')
        temp0wheather = getWeatherEmoji(hourly_json["list"][0]["weather"][0]["id"])
        temp1 = str(round((hourly_json["list"][1]["main"]["temp"]-272.15),1)) + "°C"
        temp1time = datetime.fromtimestamp(hourly_json["list"][1]["dt"], tz.gettz("Europe/Stockholm")).strftime('%H:%M')
        temp1wheather = getWeatherEmoji(hourly_json["list"][1]["weather"][0]["id"])
        temp2 = str(round((hourly_json["list"][2]["main"]["temp"]-272.15),1)) + "°C"
        temp2time = datetime.fromtimestamp(hourly_json["list"][2]["dt"], tz.gettz("Europe/Stockholm")).strftime('%H:%M')
        temp2wheather = getWeatherEmoji(hourly_json["list"][2]["weather"][0]["id"])
        
        temp_situation["updated"] = datetime.now(tz.gettz("Europe/Stockholm"))
        
        out = [temp_now, wheater_now, temp0, temp0time, temp0wheather, temp1, temp1time, temp1wheather, temp2, temp2time, temp2wheather]
        
        temp_situation["last_temp"] = out
        return out
    else:
        return temp_situation["last_temp"]

def getWeatherEmoji(weatherID):

    weatherIDstr = str(weatherID)

    # Openweathermap Weather codes and corressponding emojis
    thunderstorm = "\U0001F4A8"    # Code: 200's, 900, 901, 902, 905
    drizzle = "\U0001F4A7"         # Code: 300's
    rain = "\U00002614\U0000FE0F"            # Code: 500's
    snowflake = "\U00002744\U0000FE0F"       # Code: 600's snowflake
    # snowman = "\U000026C4"       # Code: 600's snowman, 903, 906
    atmosphere = "\U0001F301"      # Code: 700's foogy
    clearSky = "\U00002600\U0000FE0F"        # Code: 800 clear sky
    fewClouds = "\U000026C5\U0000FE0F"       # Code: 801 sun behind clouds
    clouds = "\U00002601\U0000FE0F"          # Code: 802-803-804 clouds general
    hot = "\U0001F525"             # Code: 904
    defaultEmoji = "\U0001F300"    # default emojis
    
    if weatherIDstr[0] == '2' or weatherIDstr == '900' or weatherIDstr == '901' or weatherIDstr == '902' or weatherIDstr == '905':
        return thunderstorm
    elif weatherIDstr[0] == '3':
        return drizzle
    elif weatherIDstr[0] == '5':
        return rain
    elif weatherIDstr[0] == '6' or weatherIDstr == '903' or weatherIDstr == '906':
        return snowflake # + ' ' + snowman
    elif weatherIDstr[0] == '7':
        return atmosphere
    elif weatherIDstr == '800':
        return clearSky
    elif weatherIDstr == '801':
        return fewClouds
    elif weatherIDstr == '802' or weatherIDstr == '803' or weatherIDstr == '804':
        return clouds
    elif weatherIDstr == '904':
        return hot
    else:
        return defaultEmoji
    
# -------- INIT  --------
key = os.environ["VT_KEY"]
secret = os.environ["VT_SECRET"]

print("Getting tokens")
# Give the keys and the scopes to be used (40-49) to the Auth object
auth = vasttrafik.Auth(key.strip(), secret.strip(), [40, 41, 42, 43, 44, 45, 46, 47, 48, 49])
# Initialise the API request objects
vt = vasttrafik.Reseplaneraren(auth)
ts = vasttrafik.TrafficSituations(auth)

# Stop ids
chalmers_id = 9021014001960000
chalmers_tg_id = 9021014001970000
chalmersplatsen_id = 9021014001961000
# chalmersplatsen_id = 9021014019792000 # TEST, INTE DEN RIKTIGA (Lillevrå, Kungsbacka)
kapellplatsen_id = 9021014003760000

# Traffic disruptions
situation = {
    "updated": datetime.now(tz.gettz("Europe/Stockholm")),
    "previous_shown": 0,
    "situations": get_trafficsituation()
}

temp_situation = {
    "updated": 0,
    "last_temp": 0
}

# ------- ROUTES --------

@app.route("/")
def norefresh():
    with open("index.html") as f:
        site = f.read()
    return site

@app.route("/getinfo")
def getinfo():
    # Get all the info and put it in a dict and send it off!
    deps = get_async_departures([chalmers_id, chalmers_tg_id, chalmersplatsen_id, kapellplatsen_id])

    # cdep = format_departures(get_departures(chalmers_id))
    # ctgdep = format_departures(get_departures(chalmers_tg_id))
    # cpdep = format_departures(get_departures(chalmersplatsen_id))
    # kdep = format_departures(get_departures(kapellplatsen_id))
    cdep = format_departures(deps[0])
    ctgdep = format_departures(deps[1])
    cpdep = format_departures(deps[2])
    kdep = format_departures(deps[3])
    disruptions = get_disruptions()
    temperature = get_temperature()
    menu = skolmaten.get_menu()

    d = {
        "disruptions": disruptions,
        "chalmers": cdep,
        "chalmerstg": ctgdep,
        "chalmersplatsen": cpdep,
        "kapellplatsen": kdep,
        "temperature": temperature,
        "menu": menu,
        "updated": datetime.now(tz.gettz("Europe/Stockholm")).strftime("%Y-%m-%d %H:%M:%S%z")
    }

    return json.dumps(d)
