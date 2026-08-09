import os
import time
import signal
import sys
import concurrent.futures
import requests

# ---------- Configuration (via environment variables) ----------
def get_config(key, default):
    return os.getenv(key, default)

START_POST_ID = int(get_config("START_POST_ID", 1))
END_POST_ID = int(get_config("END_POST_ID", 0))          # 0 = infinite
CONCURRENT_WORKERS = int(get_config("CONCURRENT_WORKERS", 1))
PAUSE_INTERVAL = int(get_config("PAUSE_INTERVAL", 50))   # pause every N requests
PAUSE_DURATION = int(get_config("PAUSE_DURATION", 60))   # seconds
REQUEST_TIMEOUT = int(get_config("REQUEST_TIMEOUT", 30))
MAX_RETRIES = int(get_config("MAX_RETRIES", 3))
DELAY_PER_REQUEST = float(get_config("DELAY_PER_REQUEST", 0.1))  # between submissions

# Credentials & headers (can be overridden via env)
X_ACCESS_TOKEN = get_config("X_ACCESS_TOKEN",
    "5a52768799dae017de25cccb305f08ddbed6386392619763819a91cc314ab99bbd7f88e23979be414480622e8c56711eb88357051d5f67110d5e73fb47588810acf15252bc70e27dd65a4d3c62b9019dd6b762d25a3a89a86de7b22328c12749d22326b67679e9430652c3da0f4ae88b2f659efba2a99afafe689a4878a8c48177757ea3e37dc3a46f5ca3545178c8fd6fad434a8b47f3f6075dc7e957f11629303ec7d50eddd47c84d4128f49664014369460d85276155077cdf7ccea097ed5da7c0b52a6f03e1e061fd9b093a45d64b9edc68af4832403525eb20f7d33b1470ade94b655ac5bef26a50e36de4b5d11")
ADDRESS_ID = get_config("ADDRESS_ID", "8c5dd2bf82925fc3bcf8127e39ae5a182a60244ed8c7f78ea3f08df809e3ae5a")
DEVICE_ID = get_config("DEVICE_ID", "f8455FFF3-8E05-4F50-8087-D71D37FB4F2C")
X_ACF_SENSOR_DATA = get_config("X_ACF_SENSOR_DATA", 
    "4,i,sYAJ8f76d5ugyqcOJ6suyXYI71i4xBysnEL+a7r8Sje/qoGu4jtNYeSkiM+ddD6l/LjNHJz01UC4R31kAYMqPKnsGodbLQ13wH6viWPGxpiqG+gbOSEKIgJ5eORLFQTDcFAs7kigjeMdDcMgmtYgOdz32vwbKx6VPpubf/rYg0U=,AQRu0yKNyOTnmgVhvAcbga2YXR/kkJ04opAsAMDjX2zdU0f6D7014CeISLcw33dAYpFs+1E/5vQQmmlNzuJo81red2R4JxZHTX5LN3VlC7UI4mMj89ZYZU8N9vS19I6LmaoxGv3bT6W8PMQWmaRtaC3rUWdTGY0GQc3P4kSKrnU=$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$16,10,70$$$AAQAAAAG%2f%2f%2f%2f%2f9WndQPdX3HE3taaosGNKN5crqyaMhMV0H6m3Hyh4zguxGMG6L%2f+YtrYg4hqYdWSXN1nrOzWPLgGYiwf+8sukqgTXo0jZ4+d1TzlrEh6MGFQO7neCbhZB7eC8UkS2QECYwuByIz%2f32LV%2ffN7qCCra2AcB1Qe7zW+pRyDDtdctnJZ5Ivue2GtWnASKa+9N0CZjwKS8AqT0M3YFO5qmhkpgSlW3ikbgavpwQt%2fBvTjRDGumH3EytcUfyalkCYbZ9+zB7AVGFSSKQV2FLlTJcU%2fRlNWDyqDLQA9d4hv%2fIrc1rjXnoYY2nJGgYcgx2Fc4juFBSBqFR+15KP%2f5eosPItamy6KV4C3BUfq8XWV7MUhczwHL3T7F0l486g1")

COOKIE = get_config("COOKIE",
    "_abck=8D5EB0EBF59AFBABC717E9C872505C5F~-1~YAAQtw4DF+yA67efAQAAnZTz5xA4G6X/I0LO1zvr5IQ6QnSNxsJy9tuJsAZ6mtxYPrC1KCv5Eg/iEm9c/lumF7boMCdernjsBN4ADPEMyo3cnwsvP/IsJ+JHinkI68LIYkBpSMP0kpWDumSQwuvPnUGR5p9ra9k63Bp7JyGEzGc4F3gsC87qmr6fuLfM4zyJXqQXR77m7pOYtAhO3ljpAMqqFwjBB83GagcXw1pPvyedJiF5kX0pJNco7fBWZKl8mWkofRpMcCphuMEi49rNikdXiVt54uXQAMAkUMV3GWoznjBh+hFkbTfzD6gVYSKj5kmxGJl1o3TBQstiJvV5tX60ucTLJP7yyR5Gigp2McRGeeJuqR4OHqgeqs6oDuD1T2JLVMDyzVZsej3qvXQhP2gepoNAnde4qi655YQkpg+eplBc41FswLJL6KDwPtSO2MH1NoaOCkmIL4DG+ZjAF1l4/yDc1JDIvAOeXIkDZliaitNWSbVaQQEBAdEeEod1ZCSK0FxEVmDEBoy3fDUMCFAQBFxasbQ1GY1PO7sxNisV9rI/SBd180UcMiaMkgPIT7GuYZApW03Cm5Y2a3Z0fBN34UcStvqFUIsgA9xb7gd4CsDxBco0+tsC~-1~-1~1786305488~AAQAAAAG%2f%2f%2f%2f%2f8f4XDiHT2wgYg00ZZUM5%2fuGS4vHQAVawPdpV%2f6UGmcf450%2fB3xOg9qs7iCe%2fSnRDNTCgLVWF+5CJtYQGbKuMcbI++KUA87e2aE9~-1; aopopuwtjtssi=RS_10_10_24_23_BJP_80; _ga_F433FYMYX9=GS2.1.s1786301889$o1$g1$t1786301890$j59$l0$h0; _fbp=fb.1.1786301889178.286435271536208169; _ga=GA1.1.1761276054.1786301889; _gcl_au=1.1.577038215.1786301889; ak_bmsc=A799C9819D2599B30F711EABCB433C9F~000000000000000000000000000000~YAAQzKTUFyFoctKfAQAAGrvj5wC5kDSGk4WZZRAaXET674dht0TyggvpS3Ff6XgWb2T4mp+ZCFfqi6kVV9ZRGrQauCTkeuO6xBB9492MlnfNJhgyOxQG8pnRuLn7B82Nzl+fOU2IKtKr0LyMBrhhhxFgCVPXBGgSMogsTFtEKLOsf5G2guxQQlKMf+BaBAXtoy0SSR/Qz1teDuX2j4O8LY4y691D0ipsmcyHMhscJcYe2xeymopL1w3kBmJBSshbQKxF1uA5LzOzkX8uejrmkT6W0l9E2OTrKqW7hROEeXs7f0atKdnN+kODH2gdDeztE4dnwo4tvxDWkqdLdWKSgCTdLKJ9eKItnLYW0TQCU6q6GWnOYZ/lPYMlUjUN/BkfQJtaJdlSUmAnLxdVtWwbz8+RK7IkhrJvPosCgprlf/8DtzykmjyZwqeGW1xkW2k1eRw+WgcpDrv5Vv9BwkJZioPArFOpvqggXFfsuSugArMgVwMrIp/AkVPpmRpNqs3MrVL7e+B6yUJIw9eD7jAcsPt0DM/aeYaWEF+fTpwKUE/wzjMsZZhHCdV6C2oaWdb/AB53ixcbnIskg/aSof6yOjDeRkpQIlIABIcJ6thuKiP+; _gid=GA1.2.1245722201.1786301889; bm_sz=B652C9552F7D0A718F07970402EE8A36~YAAQtw4DF+QJ6LefAQAAdrnj5wB01RmH7sTymgFaTEvA3FfkBCSIQfZofzF01Qok0zvuEzxfhXXLOc4Aw53Ycn/8/pvjrUNX6uoA1i3dKUu7CoJv72uD5LWYrITOI4vp1AwMZMVJsKSq5Ti8Ok2E7lINg51dQakS54sDCf+1C8l6BLQyXlm7rTNi4+Fhs3vdi3cH2JM1ClW6M2mAlZOtPZAxo75s+fo5x7FQ4LWHCXNUBeK+sP5SmNecrbMqtHG/DyJvhvdomX9f5h2Ah2qwS64FhWKeYPw31qou3K/ayt0AWi3Zed+FlFkuS5at02pNeiMOawqesWHX+K2kUQvJW7MW52mAjtXr3JWPgCz7RI86WbfNVU0LyTIHo6NdfXvBZd4Dyht2vg/0LdFDrlXI/B6m/epIPz+NcihOAjjXBn3LRvm9dy97eOMYSw==~4473143~3748673; bm_mi=B704E3D00318E8B27D4B33680F335614~YAAQtw4DFzcJ6LefAQAA77Xj5wAd9c6FN1IK+VvnJE1YSxWY7ZzqPV0Dm/uocvjRTW/j1IEzGRRs9O0nH3IZ7IX+o5Aur0LRIix2G2AEyqVeIDYlxJIBLyeXLck6a5fPSRjx1K3hFKJ53K3nxD0mxPGUx6xzrYalDe6cA+XVk7yJ7aW/6+Ubh/IcIzagFFCvpoMGds/eHkkqkwYD0Hk0C5VGHUW6tI0MKoqAtVpX0sBYg6ctEsJLit69GqNYhAmmU63EcoaI80hoqWQg/iO90Uyx3bLAZlR42hswgy1U0oYr9lQ1FzITkF8Kx+HtXxtEVjXFPpLKR1kHsRIBcF/CeuAg0wzbMNAGvcwLnfaqUwoZkU68B+4XxTUl9W6ZZHWb9+Tr3e4JZiCpSmeJgwaod+s3Yn6SCXdB2mSnV/I60SuH7A==~1; bm_sv=95C7970C7DB03E49D07C92C664B93F9E~YAAQtw4DFzgJ6LefAQAA77Xj5wDa+i8ac2olWmL0nzNyDlsDoZLmUzubTbWvW0YdeZZG+hYXZjjw6gpjPEz7nbtry4XVTA0QKwBUwgHUfxDD6os/PLdn23ifJ3lOsK92pnLprctlLTWr4Cb1ih4k4C+DtilyPzN4iqLig5CX4jjnSI1uFL6722jIt4zP43OmTgNSF5MsEpG1F74VSiM5wyyRzOgrx701i318nSE/Mq0veC/sdvUqcfxMf+9xXaSn5xQGzlg=~1")

# ---------- Base Headers ----------
headers = {
    "Host": "api.narendramodi.in",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-acf-sensor-data": X_ACF_SENSOR_DATA,
    "Cookie": COOKIE,
    "Connection": "close",
    "Accept": "*/*",
    "User-Agent": "Narendra Modi App/7.9 (iOS 18.5; iPhone Build/Narendra Modi App)",
    "requestFrom": "ios",
    "Accept-Language": "en-IN,en;q=0.9"
}

# ---------- Fixed form data (except post_id) ----------
BASE_DATA = {
    "relation_type": "sharewhatsapp",
    "activity": "share",
    "share_platform": "WhatsApp",
    "action": "addvolunteerpoints",
    "deviceid": DEVICE_ID,
    "X-Access-Token": X_ACCESS_TOKEN,
    "addressid": ADDRESS_ID,
    "x-app-version": "7.9",
    "apiversion": "2",
    "navigationtag": ""
}

URL = "https://api.narendramodi.in/apiv2"

# ---------- Global state ----------
shutdown_requested = False
total_processed = 0
successful = 0
failed = 0
lock = None  # will be initialized in main

# ---------- Signal handler ----------
def signal_handler(sig, frame):
    global shutdown_requested
    print("\n⚠️  Shutdown requested. Completing current tasks...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ---------- Request function ----------
def send_request(post_id):
    global shutdown_requested, total_processed, successful, failed, lock

    if shutdown_requested:
        return False

    for attempt in range(1, MAX_RETRIES + 1):
        if shutdown_requested:
            return False

        try:
            # Build data with current post_id
            data = BASE_DATA.copy()
            data["post_id"] = str(post_id)

            response = requests.post(URL, data=data, headers=headers, timeout=REQUEST_TIMEOUT)

            if response.status_code == 200:
                try:
                    json_resp = response.json()
                    status = json_resp.get("status", "unknown")
                    msg = json_resp.get("message", "")
                    print(f"✅ post_id={post_id} | {response.status_code} | {status} - {msg}")
                except:
                    print(f"✅ post_id={post_id} | {response.status_code}")
                return True

            elif response.status_code == 429:
                wait = (2 ** attempt) * 2
                print(f"⏳ post_id={post_id} | Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue

            elif response.status_code >= 500:
                wait = 2 ** attempt
                print(f"🔄 post_id={post_id} | Server error {response.status_code}, retry {attempt}/{MAX_RETRIES} in {wait}s")
                time.sleep(wait)
                continue

            else:
                print(f"❌ post_id={post_id} | Failed with {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            print(f"⏱️ post_id={post_id} | Timeout, retry {attempt}/{MAX_RETRIES} in {wait}s")
            time.sleep(wait)

        except requests.exceptions.ConnectionError as e:
            wait = 2 ** attempt
            print(f"🔌 post_id={post_id} | Connection error, retry {attempt}/{MAX_RETRIES} in {wait}s")
            time.sleep(wait)

        except Exception as e:
            print(f"❌ post_id={post_id} | Unexpected error: {e}")
            return False

    print(f"❌ post_id={post_id} | All retries exhausted")
    return False

# ---------- Main loop ----------
def main():
    global shutdown_requested, total_processed, successful, failed, lock
    lock = concurrent.futures.thread.Lock()  # for thread-safe counters

    print(f"🚀 Starting /apiv2 poster from post_id={START_POST_ID}" +
          (f" to {END_POST_ID}" if END_POST_ID else " (infinite)"))
    print(f"📊 Workers={CONCURRENT_WORKERS}, pause every {PAUSE_INTERVAL} requests for {PAUSE_DURATION}s")
    print(f"🔄 Max retries={MAX_RETRIES}, timeout={REQUEST_TIMEOUT}s")
    print("-" * 60)

    post_id = START_POST_ID
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = {}

        while True:
            if shutdown_requested:
                break

            # If END_POST_ID is set and we exceed it, finish
            if END_POST_ID and post_id > END_POST_ID:
                break

            # Submit task
            future = executor.submit(send_request, post_id)
            futures[future] = post_id
            post_id += 1

            # Limit pending futures to avoid memory blow-up
            if len(futures) >= CONCURRENT_WORKERS * 2:
                done, _ = concurrent.futures.wait(
                    futures,
                    return_when=concurrent.futures.FIRST_COMPLETED
                )
                for f in done:
                    post_id_done = futures.pop(f)
                    with lock:
                        total_processed += 1
                        if f.result():
                            successful += 1
                        else:
                            failed += 1

                    # Pause after every PAUSE_INTERVAL requests (total)
                    with lock:
                        if total_processed % PAUSE_INTERVAL == 0:
                            print(f"\n--- 📊 Processed {total_processed} total ({successful} ✅, {failed} ❌). "
                                  f"Pausing {PAUSE_DURATION}s... ---\n")
                            time.sleep(PAUSE_DURATION)

            # Small delay between submissions
            time.sleep(DELAY_PER_REQUEST)

        # Wait for remaining futures
        for f in concurrent.futures.as_completed(futures):
            if shutdown_requested:
                break
            post_id_done = futures.pop(f)
            with lock:
                total_processed += 1
                if f.result():
                    successful += 1
                else:
                    failed += 1

            with lock:
                if total_processed % PAUSE_INTERVAL == 0:
                    print(f"\n--- 📊 Processed {total_processed} total ({successful} ✅, {failed} ❌). "
                          f"Pausing {PAUSE_DURATION}s... ---\n")
                    time.sleep(PAUSE_DURATION)

    # Final summary
    print("\n" + "=" * 60)
    print(f"📊 Final Summary:")
    print(f"   Total Processed: {total_processed}")
    print(f"   Successful: {successful} ✅")
    print(f"   Failed: {failed} ❌")
    print("=" * 60)
    if shutdown_requested:
        print("🛑 Process stopped by user.")

if __name__ == "__main__":
    main()
