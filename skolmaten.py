# coding: utf-8

# Module for talking to the Skolmaten API
import os
import requests
from datetime import datetime, timedelta

updated_menu = datetime.now() - timedelta(hours=48)
menu_cached = []

def get_menu():
    global updated_menu
    global menu_cached

    if updated_menu > datetime.now() - timedelta(hours=6):
        print("Returning")
        return menu_cached

    print("Getting menu...")
    url = "https://skolmaten.se/api/3/menu/"
    # school_id = 4806606910914560
    school_id = 5582128259530752 # Testing only
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

    days = response.json().get("weeks")[0].get("days")

    # menu = []
    # for day in days:
    #     menu.append(day.get("items"))
    menu_cached = days
    updated_menu = datetime.now()
    return days
