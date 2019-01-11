# coding: utf-8
from flask import Flask, render_template
import jinja2
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("template.html", test="Hi")