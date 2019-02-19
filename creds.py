import os

with open("creds.txt") as f:
    key, secret, client_indent, client_version = f.readlines()

os.environ["VT_KEY"] = key
os.environ["VT_SECRET"] = secret
os.environ["SM_IDENT"] = client_indent
os.environ["SM_VERSION"] = client_version

# REMEMBER TO ADD import creds WHEN TESTING