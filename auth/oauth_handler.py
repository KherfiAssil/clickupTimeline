# clickup_api/auth/oauth_handler.py

import requests
import json
import os
from dotenv import load_dotenv

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

TOKEN_FILE = os.path.join(DATA_DIR, "clickup_tokens.json")

def get_access_token():
    if not os.path.exists(TOKEN_FILE):
        code = input("🔐 Entrez le code OAuth2 : ")
        return exchange_code_for_token(code)
    else:
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)
        return tokens["access_token"]

def exchange_code_for_token(code):
    url = "https://api.clickup.com/api/v2/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    res = requests.post(url, data=payload).json()
    with open(TOKEN_FILE, "w") as f:
        json.dump(res, f)
    return res["access_token"]

def refresh_token():
    with open(TOKEN_FILE) as f:
        tokens = json.load(f)
    url = "https://api.clickup.com/api/v2/oauth/token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": tokens["refresh_token"]
    }
    res = requests.post(url, data=payload).json()
    with open(TOKEN_FILE, "w") as f:
        json.dump(res, f)
    return res["access_token"]
