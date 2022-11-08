import json
import os
import pathlib
import requests
import sys
import yaml

def load_config():
    path = os.path.join(pathlib.Path(__file__).parent.absolute(), 'config.yaml')
    if os.path.isfile(path):
        with open(path, "r") as stream:
            return yaml.safe_load(stream)
    raise NotImplementedError("No configuration")

def get(url):
    config = load_config()
    url = f"{config['baseurl']}/{url}"
    headers = { "Accept": "application/vnd.github+json", "Authorization": f"Bearer {config['token']}", }
    return requests.get(url, headers=headers)

def post(url, payload):
    config = load_config()
    url = f"{config['baseurl']}/{url}"
    headers = { "Accept": "application/vnd.github+json", "Authorization": f"Bearer {config['token']}", }
    return requests.post(url, headers=headers, json=payload)

def check(response, okcodes):
    """Helper to decode response and log upon error"""
    if response.status_code in okcodes:
        return True

    print(f"Query failed, code: {response.status_code}")
    if len(response.content):
        print(response.json())

    return False
