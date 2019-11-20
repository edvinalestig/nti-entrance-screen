import os
import requests
from datetime import datetime, timezone, timedelta
import json
import dateutil.tz as tz

if "OWM_KEY" not in list(os.environ.keys()):
    with open("creds.txt") as f:
        owm_key = f.readlines()[-1]
        os.environ["OWM_KEY"] = owm_key

temp_situation = {
    "updated": 0,
    "last_temp": 0
}

def get_temperature():
    time_now = tz.gettz("Europe/Stockholm")
    if temp_situation["updated"] == 0 or temp_situation["updated"] < datetime.now(time_now) - timedelta(minutes=10):
        print("Updating temperatures")

        openweathermap_key = os.environ["OWM_KEY"]

        # Current weather
        api_call = "https://api.openweathermap.org/data/2.5/weather?q=Göteborg&APPID=" + openweathermap_key
        r = requests.get(api_call)
        r_json = json.loads(str(r.json()).replace("'", '"'))
        temp_now = str(round((r_json["main"]["temp"]-272.15), 1)) + "°C"
        wheater_now = getWeatherEmoji(r_json["weather"][0]["id"])
        
        # Call weather prognosis api
        hourly_call = "https://api.openweathermap.org/data/2.5/forecast?q=Göteborg&APPID=" + openweathermap_key
        hourly_r = requests.get(hourly_call)
        hourly_json = json.loads(str(hourly_r.json()).replace("'", '"'))

        # Weather in 3 hours
        temp0 = str(round((hourly_json["list"][0]["main"]["temp"]-272.15),1)) + "°C"
        temp0time = datetime.fromtimestamp(hourly_json["list"][0]["dt"], time_now).strftime('%H:%M')
        temp0wheather = getWeatherEmoji(hourly_json["list"][0]["weather"][0]["id"])

        # Weather in 6 hours
        temp1 = str(round((hourly_json["list"][1]["main"]["temp"]-272.15),1)) + "°C"
        temp1time = datetime.fromtimestamp(hourly_json["list"][1]["dt"], time_now).strftime('%H:%M')
        temp1wheather = getWeatherEmoji(hourly_json["list"][1]["weather"][0]["id"])

        # Weather in 9 hours
        temp2 = str(round((hourly_json["list"][2]["main"]["temp"]-272.15),1)) + "°C"
        temp2time = datetime.fromtimestamp(hourly_json["list"][2]["dt"], time_now).strftime('%H:%M')
        temp2wheather = getWeatherEmoji(hourly_json["list"][2]["weather"][0]["id"])
        
        temp_situation["updated"] = datetime.now(time_now)
        
        out = [temp_now, wheater_now, temp0, temp0time, temp0wheather, temp1, temp1time, temp1wheather, temp2, temp2time, temp2wheather]
        
        temp_situation["last_temp"] = out
        return out
    else:
        return temp_situation["last_temp"]

# Uses emoji to display the weather icon
def getWeatherEmoji(weatherID):
    weatherIDstr = str(weatherID)

    # Openweathermap Weather codes and corressponding emojis
    thunderstorm = "\U0001F4A8"        # Code: 200's, 900, 901, 902, 905
    drizzle = "\U0001F4A7"             # Code: 300's
    rain = "\U00002614\U0000FE0F"      # Code: 500's
    snowflake = "\U00002744\U0000FE0F" # Code: 600's snowflake
    # snowman = "\U000026C4"           # Code: 600's snowman, 903, 906
    atmosphere = "\U0001F301"          # Code: 700's foogy
    clearSky = "\U00002600\U0000FE0F"  # Code: 800 clear sky
    fewClouds = "\U000026C5\U0000FE0F" # Code: 801 sun behind clouds
    clouds = "\U00002601\U0000FE0F"    # Code: 802-803-804 clouds general
    hot = "\U0001F525"                 # Code: 904
    defaultEmoji = "\U0001F300"        # default emojis
    
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