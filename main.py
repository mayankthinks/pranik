import requests
import time
import signal
import sys
import concurrent.futures
from requests_toolbelt.multipart.encoder import MultipartEncoder

import os

# --- Configuration ---
# Function to get env variable with fallback to hardcoded default
def get_config(key, default):
    return os.getenv(key, default)

START_MISSION_ID = int(get_config("START_MISSION_ID", 1))
END_MISSION_ID = int(get_config("END_MISSION_ID", 100000010000))
CONCURRENT_WORKERS = int(get_config("CONCURRENT_WORKERS", 10))
DELAY_PER_REQUEST = float(get_config("DELAY_PER_REQUEST", 0.1))
PAUSE_INTERVAL = int(get_config("PAUSE_INTERVAL", 80))
PAUSE_DURATION = int(get_config("PAUSE_DURATION", 0.2))
REQUEST_TIMEOUT = int(get_config("REQUEST_TIMEOUT", 30))
MAX_RETRIES = int(get_config("MAX_RETRIES", 3))

# --- Proxy Configuration ---
# Set USE_PROXY = True and add your proxy details if running on AWS/Cloud
USE_PROXY = get_config("USE_PROXY", "False").lower() == "true"
PROXY_URL = get_config("PROXY_URL", "http://IP:PORT")

# Credentials
X_ACCESS_TOKEN = get_config("X_ACCESS_TOKEN", "5a52768799dae017de25cccb305f08ddbed6386392619763819a91cc314ab99bbd7f88e23979be414480622e8c56711eb88357051d5f67110d5e73fb47588810acf15252bc70e27dd65a4d3c62b9019dd6b762d25a3a89a86de7b22328c12749d22326b67679e9430652c3da0f4ae88b2f659efba2a99afafe689a4878a8c48177757ea3e37dc3a46f5ca3545178c8fd6fad434a8b47f3f6075dc7e957f11629303ec7d50eddd47c84d4128f49664014369460d85276155077cdf7ccea097ed5da7c0b52a6f03e1e061fd9b093a45d64b9edc68af4832403525eb20f7d33b1470ade94b655ac5bef26a50e36de4b5d11")
ADDRESS_ID = get_config("ADDRESS_ID", "8c5dd2bf82925fc3bcf8127e39ae5a182a60244ed8c7f78ea3f08df809e3ae5a")
DEVICE_ID = get_config("DEVICE_ID", "f8455FFF3-8E05-4F50-8087-D71D37FB4F2C")
TOKEN = get_config("TOKEN", "JOytkZ4Y9llcjPCw9RSy7dUORRX3uoyg6NFuLIf5rcFlFW2Wqu6KrVSckQcswUuo")

url = "https://api.narendramodi.in/apiv1"

headers_template = {
    "Host": "api.narendramodi.in",
    "Accept": "*/*",
    "Sec-Fetch-Site": "same-site",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Mode": "cors",
    "Origin": "https://www.narendramodi.in",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Referer": "https://www.narendramodi.in/",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty"
}

# Graceful shutdown flag
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global shutdown_requested
    print("\n⚠️  Shutdown requested. Completing current tasks...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def send_request_with_retry(mission_id):
    """Send request with retry logic and exponential backoff"""
    global shutdown_requested
    
    if shutdown_requested:
        return False
    
    for attempt in range(1, MAX_RETRIES + 1):
        if shutdown_requested:
            return False
            
        try:
            fields = {
                "missionid": str(mission_id),
                "missiontype": "share",
                "action": "completemission",
                "X-Access-Token": X_ACCESS_TOKEN,
                "addressid": ADDRESS_ID,
                "deviceid": DEVICE_ID,
                "apiversion": "2",
                "version": "3",
                "token": TOKEN,
                "request_source": "pwa",
                "lang": "en",
                "platform": "iOS"
            }

            m = MultipartEncoder(fields=fields)
            current_headers = headers_template.copy()
            current_headers["Content-Type"] = m.content_type

            response = requests.post(
                url, 
                data=m, 
                headers=current_headers, 
                timeout=REQUEST_TIMEOUT
            )
            
            # Validate response
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    status = json_response.get("status", "unknown")
                    message = json_response.get("message", "")
                    print(f"✅ MissionID: {mission_id} | Status: {response.status_code} | Response: {status} - {message}")
                except:
                    print(f"✅ MissionID: {mission_id} | Status: {response.status_code}")
                return True
                
            elif response.status_code == 429:
                # Rate limited - wait longer before retry
                wait_time = (2 ** attempt) * 2
                print(f"⏳ MissionID: {mission_id} | Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
                
            elif response.status_code >= 500:
                # Server error - retry with backoff
                wait_time = 2 ** attempt
                print(f"🔄 MissionID: {mission_id} | Server error {response.status_code}. Retry {attempt}/{MAX_RETRIES} in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            else:
                print(f"❌ MissionID: {mission_id} | Failed with status: {response.status_code}")
                return False
            
        except requests.exceptions.Timeout:
            wait_time = 2 ** attempt
            print(f"⏱️  MissionID: {mission_id} | Timeout. Retry {attempt}/{MAX_RETRIES} in {wait_time}s...")
            time.sleep(wait_time)
            
        except requests.exceptions.ConnectionError as e:
            wait_time = 2 ** attempt
            print(f"🔌 MissionID: {mission_id} | Connection error. Retry {attempt}/{MAX_RETRIES} in {wait_time}s...")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"❌ MissionID: {mission_id} | Error: {e}")
            return False
    
    print(f"❌ MissionID: {mission_id} | Failed after {MAX_RETRIES} retries")
    return False

def main():
    global shutdown_requested
    
    print(f"🚀 Starting process from {START_MISSION_ID} to {END_MISSION_ID}...")
    print(f"📊 Config: {CONCURRENT_WORKERS} workers, {DELAY_PER_REQUEST}s delay, pause every {PAUSE_INTERVAL} requests")
    print(f"🔄 Max retries: {MAX_RETRIES}, Timeout: {REQUEST_TIMEOUT}s")
    print("-" * 60)
    
    total_processed = 0
    successful = 0
    failed = 0
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = {}
            
            for mission_id in range(START_MISSION_ID, END_MISSION_ID + 1):
                if shutdown_requested:
                    break
                
                # Submit task
                future = executor.submit(send_request_with_retry, mission_id)
                futures[future] = mission_id
                
                # Limit pending futures to prevent memory issues
                if len(futures) >= CONCURRENT_WORKERS * 2:
                    # Wait for at least one to complete
                    done, _ = concurrent.futures.wait(
                        futures, 
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )
                    for completed_future in done:
                        try:
                            if completed_future.result():
                                successful += 1
                            else:
                                failed += 1
                        except Exception as e:
                            failed += 1
                        del futures[completed_future]
                        total_processed += 1
                
                # Pause Logic
                if total_processed > 0 and total_processed % PAUSE_INTERVAL == 0:
                    print(f"\n--- 📊 Progress: {total_processed} processed ({successful} ✅, {failed} ❌). Pausing for {PAUSE_DURATION}s... ---\n")
                    time.sleep(PAUSE_DURATION)
                
                # Small delay between submissions
                time.sleep(DELAY_PER_REQUEST)
            
            # Wait for remaining futures
            for future in concurrent.futures.as_completed(futures):
                if shutdown_requested:
                    break
                try:
                    if future.result():
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                total_processed += 1
                
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Final Summary:")
    print(f"   Total Processed: {total_processed}")
    print(f"   Successful: {successful} ✅")
    print(f"   Failed: {failed} ❌")
    print("=" * 60)
    
    if shutdown_requested:
        print("🛑 Process was stopped by user.")

if __name__ == "__main__":
    main()
