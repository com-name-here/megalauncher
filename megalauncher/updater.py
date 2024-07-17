import configparser
import os
import stat
import sys
from datetime import datetime

import requests

from util import get_location, create_config_file, get_installed_version, github_api_request


def get_release_assets(release_url):
    response_json = github_api_request(release_url)
    if not response_json:
        return None

    download_urls = []
    for asset in response_json["assets"]:
        if sys.platform == "win32" and asset["browser_download_url"].endswith(".exe"):
            download_urls.append(asset["browser_download_url"])
        elif sys.platform == "linux" and not asset["browser_download_url"].endswith((".tar.gz", ".zip", ".exe")):
            download_urls.append(asset["browser_download_url"])

    return download_urls


def check_for_updates():
    mac_path = get_location("mac_path")
    config_path = get_location("config_path")
    mac_path_exists = os.path.exists(mac_path)
    config_file = configparser.ConfigParser()

    tags_url = f"https://api.github.com/repos/MegaAntiCheat/client-backend/tags"
    response_json = github_api_request(tags_url)
    if not response_json:
        return "Failed to check for updates."

    tag = response_json[0]["name"]
    prev_tag = get_installed_version()
    release_url = f"https://api.github.com/repos/MegaAntiCheat/client-backend/releases/tags/{tag}"
    assets = get_release_assets(release_url)

    if not assets:
        return "No proper release assets found."

    download_url = assets[0]

    config_file.read(config_path)
    config_file["mac"]["last_update_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    with open(config_path, "w") as configfile:
        config_file.write(configfile)

    if tag != prev_tag or not mac_path_exists:
        download_release(download_url, mac_path)
        config_file["mac"]["version"] = tag
        with open(config_path, "w") as configfile:
            config_file.write(configfile)
        return f"{"Updated to" if mac_path_exists else "Installed"} MAC {tag}."

    return "Up to date."


def download_release(download_url, mac_path):
    path = os.path.dirname(mac_path)
    response = requests.get(download_url)

    os.makedirs(path, exist_ok=True)

    if os.path.exists(mac_path):
        os.rename(mac_path, f"{mac_path}.bak")

    with open(mac_path, "wb") as f:
        f.write(response.content)

    if sys.platform == "linux":
        os.chmod(mac_path, os.stat(mac_path).st_mode | stat.S_IXUSR)


def reinstall_mac():
    mac_path = get_location("mac_path")
    config_path = get_location("config_path")

    for file in [mac_path, f"{mac_path}.bak", config_path]:
        if os.path.exists(file):
            os.remove(file)

    create_config_file()
    return check_for_updates()
