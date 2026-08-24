#!/usr/bin/env python3
"""
Script to approve and publish content items for acceptance testing.
"""
import sys
import requests
import time

API_BASE = "http://localhost:8000/api/v1"

def login():
    """Login as admin and get token."""
    response = requests.post(f"{API_BASE}/auth/login", json={
        "username": "admin",
        "password": "admin"
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        sys.exit(1)

def approve_content(token, content_id):
    """Approve a content item."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/content/{content_id}/approve", headers=headers)
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

def main():
    content_ids = [
        "content-842eb828-b3a0-4d16-b32e-d28f6dfc6a1b",
        "content-7c442249-b196-4cdd-8444-5362fa648683",
        "content-3d345810-b400-4b45-b9f7-f8e383b86847",
        "content-66599799-e7c6-431c-9478-9f2c97f7bce4"
    ]

    print("Logging in as admin...")
    token = login()
    print("Logged in successfully")

    print("\nApproving and publishing content items...")
    for content_id in content_ids:
        print(f"\nProcessing {content_id}...")
        if approve_content(token, content_id):
            time.sleep(1)  # Small delay between operations
            publish_content(token, content_id)
        time.sleep(2)  # Delay between items

    print("\nContent approval and publishing completed")

if __name__ == "__main__":
    main()
