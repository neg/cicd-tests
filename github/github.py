import json
import os
import pathlib
import requests
import sys
import yaml

def load_config():
    def load_yaml(file):
        path = os.path.join(pathlib.Path(__file__).parent.absolute(), file)
        if os.path.isfile(path):
            with open(path, "r") as stream:
                return yaml.safe_load(stream)

        return None

    def validate(config):
        if config is None:
            raise NotImplementedError("No configuration found")

        if 'token' in config:
            raise KeyError("Token stored in configuration")

        for section in ['code', 'test']:
            if section not in config:
                raise KeyError(f"Missing section in configuration ({section})")

            for key in ['api', 'repo']:
                if key not in config[section]:
                    raise KeyError(f"Missing key ({key}) in configuration {section}")

    def pat():
        """Retrieve the GitHub PAT in a somewhat sane way"""

        # Primary source is environment. This is the primary method and should
        # be used when running on public infrastructure
        if 'PAT' in os.environ:
            return os.environ['PAT']

        # Fallback source is the secret configuration file
        # NOTE: This file should never be committed to git history. It exists
        # only to allow triggering WebHook chains to work around GitHub
        # limitations.
        secret = load_yaml("secret.yaml")
        if secret is not None and 'token' in secret:
            return secret['token']

        raise NotImplementedError("No PAT token found from secure source")

    # Load and validate configuration
    config = load_yaml('config.yaml')
    validate(config)

    # Inject the GitHub PAT token
    config['token'] = pat()

    return config

def get(sec, url):
    config = load_config()
    url = f"{config[sec]['api']}/{url}"
    headers = { "Accept": "application/vnd.github+json", "Authorization": f"Bearer {config['token']}", }
    return requests.get(url, headers=headers)

def post(sec, url, payload):
    config = load_config()
    url = f"{config[sec]['api']}/{url}"
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
