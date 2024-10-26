import configparser
import ctypes
import os
import re
import signal
import subprocess
import sys
import threading
from datetime import datetime, timedelta

from updater import check_for_updates
from util import start_separate_process, check_if_process_running, get_location

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[mz]")
TIMESTAMP_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\s+")


def process_output(line):
    line = ANSI_ESCAPE.sub("", line).replace("[0m", "").strip()
    line = TIMESTAMP_REGEX.sub("", line)
    return line


def capture_output(process, callback, stop_event):
    for line in iter(process.stdout.readline, ""):
        if stop_event.is_set():
            break
        processed_line = process_output(line)
        if processed_line:
            callback(processed_line)


class MACLauncher:
    def __init__(self):
        self.mac_process = None
        self.output_thread = None
        self.stop_event = threading.Event()
        self.observers = []

    def launch(self, launch_with_tf2, output_callback):
        mac_path = get_location("mac_path")
        config_path = get_location("config_path")
        config = configparser.ConfigParser()
        config.read(config_path)

        if self._should_check_for_updates(config, mac_path):
            if output_callback:
                output_callback("Checking for updates...")
            update_response = check_for_updates()
            if output_callback:
                output_callback(update_response)

        if launch_with_tf2:
            if output_callback:
                output_callback("Launching TF2...")
            launch_error = self._launch_tf2()
            if launch_error == "tf2_running":
                if output_callback:
                    output_callback("TF2 is already running.")

        if output_callback:
            output_callback("Launching MAC...")
        self.mac_process = self._launch_mac()

        if self.mac_process:
            self.stop_event.clear()
            self.output_thread = threading.Thread(
                target=capture_output,
                args=(self.mac_process, output_callback, self.stop_event)
            )
            self.output_thread.start()
        elif output_callback:
            output_callback("Failed to launch MAC")

    def stop(self):
        if self.mac_process:
            self.stop_event.set()
            if sys.platform == "win32":
                os.kill(self.mac_process.pid, signal.SIGTERM)
            else:
                os.kill(self.mac_process.pid, signal.SIGINT)
            self.mac_process.wait()
            self.output_thread.join()
            self.mac_process = None
            self.output_thread = None
        self._notify_observers()

    def is_running(self):
        return self.mac_process and self.mac_process.poll() is None

    def check_status(self):
        if self.mac_process and self.mac_process.poll() is not None:
            self.mac_process = None
            self.output_thread = None
            self._notify_observers()

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def _notify_observers(self):
        for observer in self.observers:
            observer()

    @staticmethod
    def _should_check_for_updates(config, mac_path):
        macinfo = config["mac"]
        last_update_check = macinfo.get("last_update_check", "")
        current_date = datetime.now()

        if last_update_check and any(char.isdigit() for char in last_update_check):
            last_update_form = datetime.strptime(last_update_check, "%Y-%m-%d %H:%M:%S.%f")
            return current_date >= last_update_form + timedelta(days=1) or not os.path.exists(mac_path)
        return True

    @staticmethod
    def _launch_tf2():
        tf2_exe = "tf_win64" if sys.platform == "win32" else "tf_linux64"
        if check_if_process_running(tf2_exe):
            return "tf2_running"
        start_separate_process("start steam://rungameid/440" if sys.platform == "win32"
                               else "xdg-open steam://rungameid/440")

    @staticmethod
    def _launch_mac():
        try:
            mac_path = get_location("mac_path")
            return subprocess.Popen(
                [mac_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
        except KeyboardInterrupt:
            return None


mac_launcher = MACLauncher()


def main(launch_with_tf2=True, output_callback=None):
    mac_launcher.launch(launch_with_tf2, output_callback)


def stop_mac():
    mac_launcher.stop()


def is_mac_running():
    return mac_launcher.is_running()


def check_mac_status():
    mac_launcher.check_status()
