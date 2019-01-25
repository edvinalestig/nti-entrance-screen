import os

with open("creds.txt") as f:
    key, secret = f.readlines()

os.environ["VT_KEY"] = key
os.environ["VT_SECRET"] = secret

# REMEMBER TO ADD import creds WHEN TESTING