# =============================================================================
# MIT License
# 
# Copyright (c) 2021 luckytyphlosion
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# =============================================================================

import requests
import re
import traceback
import time
import subprocess
import datetime
from abc import ABC, abstractmethod
import json
import argparse

CHADSOFT_STATUS_URL = "https://www.chadsoft.co.uk/online-status/status.txt"
countdown_status_regex = re.compile(r"<h1>COUNTDOWN STATUS: ([^<]+)</h1>")
x_players_regex = re.compile(r"^([0-9]+) players")

good_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789., ")

class CountdownNotifier(ABC):
    __slots__ = ("prev_online_status",)

    def __init__(self):
        super().__init__()
        self.prev_online_status = ""

    def wait_status_change(self):
        exception_sleep_time = 15
        while True:
            try:
                r = requests.get(CHADSOFT_STATUS_URL)
                if r.status_code == 200:
                    if r.text != "":
                        response_text = r.text
                        match_obj = countdown_status_regex.search(response_text)
                        if not match_obj:
                            print("Warning: Could not find online status message.")
                        else:
                            online_status = match_obj.group(1)
                            if online_status != self.prev_online_status:
                                self.on_status_change(online_status)
                                self.prev_online_status = online_status
    
                        sleep_time = 180
                    else:
                        print(f"Chadsoft status returned empty!")
                        sleep_time = 30
                else:
                    print(f"chadsoft returned {r.status_code}: {r.reason}")
                    sleep_time = 180
    
                exception_sleep_time = 15
                time.sleep(sleep_time)
            except Exception as e:
                print(f"Exception occurred: {e}\n{''.join(traceback.format_tb(e.__traceback__))}\nSleeping for {exception_sleep_time} seconds now.")
                time.sleep(exception_sleep_time)
                exception_sleep_time *= 2
                if exception_sleep_time > 1000:
                    print("Exception happened too many times! Exiting.")
                    return

    @abstractmethod
    def on_status_change(self):
        pass

def keep_only_safe_chars(s):
    return "".join([c for c in s if c in good_chars])

def send_notification(wav_file, status):
    # not secure fix me!
    #subprocess.run(["powershell.exe", "-c", f"(New-Object Media.SoundPlayer \"{wav_file}\").PlaySync();"])
    subprocess.run(["powershell.exe", "-ExecutionPolicy", "RemoteSigned", "-Command", f"New-BurntToastNotification -Text \"COUNTDOWN STATUS\", \"{keep_only_safe_chars(status)}\""])

class LocalCountdownNotifier(CountdownNotifier):
    def __init__(self):
        super().__init__()

    def on_status_change(self, online_status):
        send_notification("notification.wav", online_status)
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}] COUNTDOWN STATUS: {online_status}")

def get_player_count_from_online_status(online_status):
    if online_status == "There are no active Countdown Rooms.":
        return 0
    elif "1 player" in online_status:
        return 1
    else:
        match_obj = x_players_regex.match(online_status)
        if match_obj:
            num_players = int(match_obj.group(1))
            return min(num_players, 12)
        else:
            raise RuntimeError(f"Error: unexpected online status message \"{online_status}\"")

class DiscordCountdownNotifier(CountdownNotifier):
    __slots__ = ("prev_num_players", "roles", "webhook_url")

    def __init__(self, config_filename):
        super().__init__()
        self.prev_num_players = 0
        with open(config_filename, "r") as f:
            config = json.load(f)

        self.roles = config["roles"]
        if len(self.roles) != 12:
            raise RuntimeError("Number of roles must be 12!")

        self.webhook_url = config["webhook_url"]

    def on_status_change(self, online_status):
        num_players = get_player_count_from_online_status(online_status)
        if num_players != 0 and num_players > self.prev_num_players:
            roles_to_mention_str = " ".join(self.roles[self.prev_num_players:num_players])
        else:
            roles_to_mention_str = ""

        output_message = f"COUNTDOWN STATUS: {online_status} {roles_to_mention_str}"
        #print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}] {output_message}")
        payload ={
            "username": "MKW Countdown Notifs",
            "content": output_message,
        }

        r = requests.post(f"{self.webhook_url}?wait=true", json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Discord returned {r.status_code}: {r.reason}")

        self.prev_num_players = num_players

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", help="Notification mode to use (local or discord).")
    args = ap.parse_args()

    if args.mode == "local":
        cd_notifier = LocalCountdownNotifier()
    elif args.mode == "discord":
        cd_notifier = DiscordCountdownNotifier("config.json")
    else:
        print("Invalid mode selected!")

    cd_notifier.wait_status_change()

if __name__ == "__main__":
    main()
