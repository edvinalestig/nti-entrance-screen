import os

with open("creds.txt") as f:
    key, secret, client_indent, client_version, openweathermap_key = f.readlines()

os.environ["VT_KEY"] = key
os.environ["VT_SECRET"] = secret
os.environ["SM_IDENT"] = client_indent
os.environ["SM_VERSION"] = client_version
os.environ["OWM_KEY"] = openweathermap_key

# REMEMBER TO ADD import creds WHEN TESTING