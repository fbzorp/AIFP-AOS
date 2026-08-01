"""
Locust load testing configuration for AIFP-AOS API.
Targets read-only and enqueue paths only - no live payment execution.
Includes JWT authentication for realistic production load testing.
"""

from locust import HttpUser, task, between
import random
import jwt
from datetime import datetime, timedelta, timezone


def create_test_token(role="viewer"):
    """Create a JWT token for load testing using the application's secret."""
    from apps.api.config import settings
    secret = settings.SECRET_KEY
    payload = {
        "sub": f"load_test_user_{random.randint(1, 10000)}",
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, secret, algorithm="HS256")


class AIFPUser(HttpUser):
    """
    Simulated user for load testing AIFP-AOS API.
    Uses read-only and enqueue paths only with JWT authentication.
    """
    wait_time = between(1, 3)
    
    def on_start(self):
        """Run on start - health check and token setup."""
        self.client.get("/health")
        self.headers = {
            "Authorization": f"Bearer {create_test_token('viewer')}"
        }
    
    @task(3)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")
    
    @task(2)
    def content_queue(self):
        """Content queue endpoint (read-only)."""
        self.client.get("/api/v1/content", headers=self.headers)
    
    @task(2)
    def approvals_list(self):
        """Approvals list endpoint (read-only)."""
        self.client.get("/api/v1/approvals", headers=self.headers)
    
    @task(1)
    def payments_list(self):
        """Payments list endpoint (read-only)."""
        self.client.get("/api/v1/payments/", headers=self.headers)
    
    @task(1)
    def engagement_proposals(self):
        """Engagement proposals endpoint (read-only)."""
        self.client.get("/api/v1/engagement/proposals", headers=self.headers)
    
    @task(1)
    def calendar(self):
        """Calendar endpoint (read-only)."""
        self.client.get("/api/v1/calendar", headers=self.headers)
    
    @task(1)
    def root_endpoint(self):
        """Root endpoint."""
        self.client.get("/")


class ContentUser(HttpUser):
    """
    Simulated content-focused user.
    Tests content submission workflow (enqueue only) with operator auth.
    """
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup operator token for content operations."""
        self.headers = {
            "Authorization": f"Bearer {create_test_token('operator')}"
        }
    
    @task(3)
    def view_content_queue(self):
        """View content queue."""
        self.client.get("/api/v1/content", headers=self.headers)
    
    @task(1)
    def view_calendar(self):
        """View calendar."""
        self.client.get("/api/v1/calendar", headers=self.headers)


class ApprovalUser(HttpUser):
    """
    Simulated approval-focused user.
    Tests approval workflow endpoints with operator auth.
    """
    wait_time = between(3, 6)
    
    def on_start(self):
        """Setup operator token for approval operations."""
        self.headers = {
            "Authorization": f"Bearer {create_test_token('operator')}"
        }
    
    @task(3)
    def view_approvals(self):
        """View approvals list."""
        self.client.get("/api/v1/approvals", headers=self.headers)
    
    @task(1)
    def view_content_queue(self):
        """View content queue for approval decisions."""
        self.client.get("/api/v1/content", headers=self.headers)
    
    @task(1)
    def view_proposals(self):
        """View engagement proposals."""
        self.client.get("/api/v1/engagement/proposals", headers=self.headers)