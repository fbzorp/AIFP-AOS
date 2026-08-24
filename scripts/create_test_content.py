import sys
import requests
import time
from jose import jwt
from datetime import datetime, timedelta, timezone

API_BASE = "http://localhost:8000/api/v1"
SECRET_KEY = "StrongProductionSecretKey123!ChangeThisInProduction"

def create_test_token():
    """Create a test JWT token with admin role."""
    payload = {
        "sub": "test_user",
        "role": "founder_admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def create_content(token, title, body, channel):
    """Create a content item."""
    headers = {"Authorization": f"Bearer {token}"}
    content_data = {
        "title": title,
        "body": body,
        "channel": channel,
        "objective": "Acceptance test content",
        "target_audience": "General audience",
        "format": "post",
        "author_agent": "acceptance_test",
        "status": "draft"
    }
    response = requests.post(f"{API_BASE}/content", headers=headers, json=content_data)
    if response.status_code == 200:
        content = response.json()
        print(f"Created content: {content['id']} - {title}")
        return content['id']
    else:
        print(f"Failed to create content: {response.text}")
        return None

def approve_content(token, content_id):
    """Approve a content item."""
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
    """Publish a content item."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/content/{content_id}/publish", headers=headers)
    if response.status_code == 200:
        print(f"Published {content_id}")
        return True
    else:
        print(f"Failed to publish {content_id}: {response.text}")
        return False

# Create test token
print("Creating test token...")
token = create_test_token()
print("Test token created successfully")

# Create X content
print("\nCreating X content...")
x_content_id = create_content(token, "Acceptance Test - X Post", "This is an acceptance test post for X/Twitter verification. #AiFinPay #AI #Finance", "twitter")

# Create Telegram content
print("\nCreating Telegram content...")
telegram_content_id = create_content(token, "Acceptance Test - Telegram Post", "This is an acceptance test post for Telegram verification.", "telegram")

# Create Moltbook content
print("\nCreating Moltbook content...")
moltbook_content_id = create_content(token, "Acceptance Test - Moltbook Post", "This is an acceptance test post for Moltbook verification.", "moltbook")

# Create SEO content
print("\nCreating SEO content...")
seo_content_id = create_content(token, "Acceptance Test - SEO Content", "This is an acceptance test post for SEO verification.", "google")

content_ids = [x_content_id, telegram_content_id, moltbook_content_id, seo_content_id]

# Approve and publish all content
print("\nApproving and publishing content items...")
approved_count = 0
published_count = 0
for content_id in content_ids:
    if content_id:
        print(f"\nProcessing {content_id}...")
        if approve_content(token, content_id):
            approved_count += 1
            time.sleep(1)
            if publish_content(token, content_id):
                published_count += 1
        time.sleep(2)

print(f"\nContent creation and publishing completed. Approved {approved_count}/{len(content_ids)} items, Published {published_count}/{len(content_ids)} items")
