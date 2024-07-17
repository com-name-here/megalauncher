import configparser
import os
import subprocess
import sys
from functools import lru_cache

import psutil
import requests


class GitHubAPIError(Exception):
    pass


def create_config_file():
    config_path = get_location("config_path")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    config = configparser.ConfigParser()
    config["mac"] = {"version": "", "last_update_check": ""}
    config["launcher"] = {"tf2_checkbox": "False"}

    save_config(config)


def load_config():
    config = configparser.ConfigParser()
    config_path = get_location("config_path")

    if not os.path.exists(config_path):
        create_config_file()

    config.read(config_path)
    return config


def save_config(config):
    config_path = get_location("config_path")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, "w") as configfile:
        config.write(configfile)


@lru_cache(maxsize=None)
def get_location(location):
    if sys.platform == "win32":
        base_path = os.path.join(os.environ["APPDATA"], "megalauncher")
        locations = {
            "mac_path": os.path.join(base_path, "client_backend.exe"),
            "config_path": os.path.join(base_path, "config.ini")
        }
    else:
        locations = {
            "mac_path": os.path.join(os.path.expanduser("~"), ".local", "bin", "client_backend"),
            "config_path": os.path.join(os.path.expanduser("~"), ".config", "megalauncher", "config.ini")
        }

    return locations.get(location)


def get_installed_version():
    config_path = get_location("config_path")

    if os.path.exists(config_path):
        config = load_config()
        version = config["mac"]["version"]

        return version if version and any(char.isdigit() for char in version) else None
    else:
        print("Config file not found")
        create_config_file()
        return None


def check_if_process_running(process_name):
    return any(process_name.lower() in proc.name().lower() for proc in psutil.process_iter(["name"]))


def start_separate_process(command):
    if sys.platform == "win32":
        cwd = os.path.join(os.environ["APPDATA"], "MAC", "MACClient")
        subprocess.Popen(command, cwd=cwd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        cwd = os.path.join(os.path.expanduser("~"), ".config", "megalauncher")
        subprocess.Popen(command, cwd=cwd, shell=True, start_new_session=True)


def github_api_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response_json = response.json()

        remaining_requests = int(response.headers.get("X-RateLimit-Remaining", 0))
        print(f"Remaining Requests: {remaining_requests}")

        if remaining_requests == 0:
            raise GitHubAPIError("GitHub API rate limit exceeded!")

        return response_json

    except requests.RequestException as e:
        print(f"Connection Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
