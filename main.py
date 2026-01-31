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

START_POST_ID = int(get_config("START_POST_ID", 458660))
END_POST_ID = int(get_config("END_POST_ID", 100000000))
CONCURRENT_WORKERS = int(get_config("CONCURRENT_WORKERS", 10))
DELAY_PER_REQUEST = float(get_config("DELAY_PER_REQUEST", 0.01))
PAUSE_INTERVAL = int(get_config("PAUSE_INTERVAL", 100))
PAUSE_DURATION = int(get_config("PAUSE_DURATION", 2))
REQUEST_TIMEOUT = int(get_config("REQUEST_TIMEOUT", 30))
MAX_RETRIES = int(get_config("MAX_RETRIES", 3))

# --- Proxy Configuration ---
# Set USE_PROXY = True and add your proxy details if running on AWS/Cloud
USE_PROXY = get_config("USE_PROXY", "False").lower() == "true"
PROXY_URL = get_config("PROXY_URL", "http://IP:PORT")

# Credentials
X_ACCESS_TOKEN = get_config("X_ACCESS_TOKEN", "042d8d8c71ba8f8cdf74c425df4cfa09ca264d48152805b0fd24acd79882fd7c17ad194f10e5ea18ca10e9191a9dd767d41272f5c08aa010fc24fc23a200293b9e0769f542029858a67de02139c308a6eb4e06f1f6205470bd5618235a2bbf294fbd2508fb29d71e3c1523f98103e18b52fe7fb3cfb5b2979a3a7dbb3ff1efb25d218a367ead9d8c6e2dbe6df5455a73446f129f6c9b0815a6b45e615ab0199bc827308489aa42864d24d4274da32606775f39a4e1792ace345ad3bb5747be97f262c743bc084dc63c8206e292c838348bb9b5d803727ad0d3c65752f11f59ab05decdf3a00ca2347aa2ee2be9b22656")
ADDRESS_ID = get_config("ADDRESS_ID", "ca3d409c53607c5762854d7cc80bf0e0244323643a4dcca4d83a351d43045b27")
DEVICE_ID = get_config("DEVICE_ID", "f943fcbb-82a0-4003-342f-33e9e5d95d7e")
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

def send_request_with_retry(post_id):
    """Send request with retry logic and exponential backoff"""
    global shutdown_requested
    
    if shutdown_requested:
        return False
    
    for attempt in range(1, MAX_RETRIES + 1):
        if shutdown_requested:
            return False
            
        try:
            fields = {
                "image": "",
                "comment": "Jai Bjp",
                "type": "news-updates",
                "postid": str(post_id),
                "title": "",
                "subcomment": "No",
                "action": "postcomment",
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
                    print(f"✅ PostID: {post_id} | Status: {response.status_code} | Response: {status} - {message}")
                except:
                    print(f"✅ PostID: {post_id} | Status: {response.status_code}")
                return True
                
            elif response.status_code == 429:
                # Rate limited - wait longer before retry
                wait_time = (2 ** attempt) * 2
                print(f"⏳ PostID: {post_id} | Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
                
            elif response.status_code >= 500:
                # Server error - retry with backoff
                wait_time = 2 ** attempt
                print(f"🔄 PostID: {post_id} | Server error {response.status_code}. Retry {attempt}/{MAX_RETRIES} in {wait_time}s...")
                time.sleep(wait_time)
                continue
                
            else:
                print(f"❌ PostID: {post_id} | Failed with status: {response.status_code}")
                return False
            
        except requests.exceptions.Timeout:
            wait_time = 2 ** attempt
            print(f"⏱️  PostID: {post_id} | Timeout. Retry {attempt}/{MAX_RETRIES} in {wait_time}s...")
            time.sleep(wait_time)
            
        except requests.exceptions.ConnectionError as e:
            wait_time = 2 ** attempt
            print(f"🔌 PostID: {post_id} | Connection error. Retry {attempt}/{MAX_RETRIES} in {wait_time}s...")
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"❌ PostID: {post_id} | Error: {e}")
            return False
    
    print(f"❌ PostID: {post_id} | Failed after {MAX_RETRIES} retries")
    return False

def main():
    global shutdown_requested
    
    print(f"🚀 Starting process from {START_POST_ID} to {END_POST_ID}...")
    print(f"📊 Config: {CONCURRENT_WORKERS} workers, {DELAY_PER_REQUEST}s delay, pause every {PAUSE_INTERVAL} requests")
    print(f"🔄 Max retries: {MAX_RETRIES}, Timeout: {REQUEST_TIMEOUT}s")
    print("-" * 60)
    
    total_processed = 0
    successful = 0
    failed = 0
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
            futures = {}
            
            for post_id in range(START_POST_ID, END_POST_ID + 1):
                if shutdown_requested:
                    break
                
                # Submit task
                future = executor.submit(send_request_with_retry, post_id)
                futures[future] = post_id
                
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