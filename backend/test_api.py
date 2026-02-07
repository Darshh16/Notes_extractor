"""
Quick test script to check if the backend is working
"""
import requests
import time

API_URL = "http://localhost:8000"

print("Testing YouTube Notes Extractor API...")
print("="*60)

# Test 1: Check if server is running
print("\n1. Testing server connection...")
try:
    response = requests.get(f"{API_URL}/")
    print(f"✓ Server is running: {response.json()}")
except Exception as e:
    print(f"✗ Server connection failed: {e}")
    print("Make sure the backend is running: python main.py")
    exit(1)

# Test 2: Start extraction
print("\n2. Starting extraction...")
test_url = "https://www.youtube.com/watch?v=D_wNQR3Lee"  # Replace with a valid URL
try:
    response = requests.post(
        f"{API_URL}/api/extract",
        json={"url": test_url, "quality": "720p"}
    )
    data = response.json()
    job_id = data["job_id"]
    print(f"✓ Extraction started")
    print(f"  Job ID: {job_id}")
    print(f"  Status: {data['status']}")
    print(f"  Message: {data['message']}")
except Exception as e:
    print(f"✗ Extraction failed: {e}")
    exit(1)

# Test 3: Poll for status
print("\n3. Monitoring progress...")
print("-"*60)
for i in range(60):  # Poll for up to 2 minutes
    try:
        response = requests.get(f"{API_URL}/api/status/{job_id}")
        data = response.json()
        
        status = data["status"]
        progress = data["progress"]
        message = data["message"]
        
        print(f"\r[{progress:3d}%] {status:12s} - {message}", end="", flush=True)
        
        if status == "completed":
            print(f"\n\n✓ Extraction completed successfully!")
            print(f"  Download URL: {API_URL}/api/download/{job_id}")
            break
        elif status == "failed":
            print(f"\n\n✗ Extraction failed!")
            print(f"  Error: {data.get('error', 'Unknown error')}")
            break
        
        time.sleep(2)
    except Exception as e:
        print(f"\n✗ Status check failed: {e}")
        break
else:
    print(f"\n\n⚠ Timeout: Extraction is taking longer than expected")

print("\n" + "="*60)
print("Test complete!")
