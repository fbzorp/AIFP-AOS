"""
Locust load testing configuration for AIFP-AOS API.
Targets read-only and enqueue paths only - no live payment execution.
"""

from locust import HttpUser, task, between
import random


class AIFPUser(HttpUser):
    """
    Simulated user for load testing AIFP-AOS API.
    Uses read-only and enqueue paths only.
    """
    wait_time = between(1, 3)
    
    def on_start(self):
        """Run on start - health check."""
        self.client.get("/health")
    
    @task(3)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")
    
    @task(2)
    def content_queue(self):
        """Content queue endpoint (read-only)."""
        self.client.get("/api/v1/content")
    
    @task(2)
    def approvals_list(self):
        """Approvals list endpoint (read-only)."""
        self.client.get("/api/v1/approvals")
    
    @task(1)
    def payments_list(self):
        """Payments list endpoint (read-only)."""
        self.client.get("/api/v1/payments/")
    
    @task(1)
    def engagement_proposals(self):
        """Engagement proposals endpoint (read-only)."""
        self.client.get("/api/v1/engagement/proposals")
    
    @task(1)
    def root_endpoint(self):
        """Root endpoint."""
        self.client.get("/")


class ContentUser(HttpUser):
    """
    Simulated content-focused user.
    Tests content submission workflow (enqueue only).
    """
    wait_time = between(2, 5)
    
    @task(3)
    def view_content_queue(self):
        """View content queue."""
        self.client.get("/api/v1/content")
    
    @task(1)
    def submit_content(self):
        """Submit content for review (enqueue only)."""
        # Generate random content data
        content_data = {
            "title": f"Test Content {random.randint(1, 1000)}",
            "body": "This is test content for load testing purposes.",
            "author_agent": "LoadTestBot",
            "variants": []
        }
        # Note: This will fail without proper auth, but tests the endpoint
        self.client.post("/api/v1/content", json=content_data)


class ApprovalUser(HttpUser):
    """
    Simulated approval-focused user.
    Tests approval workflow endpoints.
    """
    wait_time = between(3, 6)
    
    @task(3)
    def view_approvals(self):
        """View approvals list."""
        self.client.get("/api/v1/approvals")
    
    @task(1)
    def view_content_queue(self):
        """View content queue for approval decisions."""
        self.client.get("/api/v1/content")