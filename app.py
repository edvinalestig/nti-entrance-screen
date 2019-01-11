# coding: utf-8
from flask import Flask, render_template
import vasttrafik

app = Flask(__name__)

with open("creds.txt") as f:
    key, secret = f.readlines()

vt = vasttrafik.Reseplaneraren(key.strip(), secret.strip(), 1)

@app.route("/")
def index():
    stop_id = vt.location_name(input="Chalmers").get("LocationList").get("StopLocation")[0].get("id")
    return render_template("template.html", test=stop_id)