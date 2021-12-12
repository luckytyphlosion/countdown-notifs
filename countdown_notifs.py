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

CHADSOFT_STATUS_URL = "https://www.chadsoft.co.uk/online-status/status.txt"
countdown_status_regex = re.compile(r"<h1>COUNTDOWN STATUS: ([^<]+)</h1>")

good_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789., ")

def keep_only_safe_chars(s):
    return "".join([c for c in s if c in good_chars])

def send_notification(wav_file, status):
    # not secure fix me!
    #subprocess.run(["powershell.exe", "-c", f"(New-Object Media.SoundPlayer \"{wav_file}\").PlaySync();"])
    subprocess.run(["powershell.exe", "-ExecutionPolicy", "RemoteSigned", "-Command", f"New-BurntToastNotification -Text \"COUNTDOWN STATUS\", \"{keep_only_safe_chars(status)}\""])

def main():
    prev_online_status = ""

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
                        if online_status != prev_online_status:
                            send_notification("notification.wav", online_status)
                            prev_online_status = online_status
                            print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %I:%m %p')}] COUNTDOWN STATUS: {online_status}")

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

if __name__ == "__main__":
    main()
