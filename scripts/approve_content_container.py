import sys
import os
import requests
import time
from jose import jwt
from datetime import datetime, timedelta, timezone

API_BASE = "http://localhost:8000/api/v1"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

def create_test_token():
    """Create a test JWT token with admin role."""
    payload = {
        "sub": "test_user",
        "role": "founder_admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def approve_content(token, content_id):
    headers = {"Authorization": f"Bearer {token}"}
    approval_data = {
        "approved_by": "acceptance_test",
        "expires_in_hours": 24,
        "reason": "Acceptance test approval"
    }
    response = requests.post(f"{API_BASE}/content/{content_id}/approve", headers=headers, json=approval_data)
    if response.status_code == 200:
        print(f"Approved {content_id}")
        return True
    else:
        print(f"Failed to approve {content_id}: {response.text}")
        return False

def publish_content(token, content_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/content/{content_id}/publish", headers=headers)
    if response.status_code == 200:
        print(f"Published {content_id}")
        return True
    else:
        print(f"Failed to publish {content_id}: {response.text}")
        return False

content_ids = [
    "content-842eb828-b3a0-4d16-b32e-d28f6dfc6a1b",
    "content-7c442249-b196-4cdd-8444-5362fa648683",
    "content-3d345810-b400-4b45-b9f7-f8e383b86847",
    "content-66599799-e7c6-431c-9478-9f2c97f7bce4"
]

print("Creating test token...")
token = create_test_token()
print("Test token created successfully")

print("\nApproving and publishing content items...")
approved_count = 0
published_count = 0
for content_id in content_ids:
    print(f"\nProcessing {content_id}...")
    if approve_content(token, content_id):
        approved_count += 1
        time.sleep(1)
        publish_result = publish_content(token, content_id)
        if publish_result:
            published_count += 1
    time.sleep(2)

print(f"\nContent approval and publishing completed. Approved {approved_count}/{len(content_ids)} items, Published {published_count}/{len(content_ids)} items")
