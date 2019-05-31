# coding: utf-8

# Module for talking to the Skolmaten API
import os
import requests
from datetime import datetime, timedelta

# Setting it to 2 days ago so it updates the first time
updated_menu = datetime.now() - timedelta(hours=48)
menu_cached = []

# When the keys are not already stored in environment variables
# This is used when running locally (testing)
if "SM_IDENT" not in list(os.environ.keys()) or "SM_VERSION" not in list(os.environ.keys()):
    with open("creds.txt") as f:
        key, secret, client_indent, client_version = f.readlines()
    os.environ["SM_IDENT"] = client_indent
    os.environ["SM_VERSION"] = client_version


def get_menu():
    global updated_menu
    global menu_cached

    if updated_menu > datetime.now() - timedelta(hours=6):
        # The info was updated in the last 6 hours
        # A new call to the API is not needed
        return menu_cached

    # Stuff for the request
    url = "https://skolmaten.se/api/3/menu/"
    school_id = 4806606910914560
    # school_id = 5582128259530752 # Testing only
    client_ident = os.environ["SM_IDENT"].strip()
    client_version = os.environ["SM_VERSION"].strip()

    header = {
        "Client": client_ident,
        "ClientVersion": client_version
    }
    params = {
        "school": school_id
    }

    response = requests.get(url, headers=header, params=params)
    if response.status_code != 200:
        print("Error!", response.status_code)
        return None

    # Get the important info from the json response
    days = response.json().get("weeks")[0].get("days")

    menu_cached = days
    updated_menu = datetime.now()
    return days
