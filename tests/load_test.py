"""
Load Testing for Customer Success FTE
Uses Locust framework as specified in hackathon requirements.

Run with: locust -f tests/load_test.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import random
import json
import time


class WebFormUser(HttpUser):
    """Simulate users submitting support forms."""
    wait_time = between(2, 10)
    weight = 3  # Web form is most common

    categories = ['general', 'technical', 'billing', 'bug_report', 'feedback']
    subjects = [
        "Help with API integration",
        "Can't login to my account",
        "Feature request: dark mode",
        "Billing question about charges",
        "Bug: file upload not working",
        "How to add team members",
        "Slack integration not syncing",
        "Need help with Gantt chart",
        "Password reset not working",
        "Question about data export",
    ]
    messages = [
        "I've been trying to use the API but keep getting 401 errors. I've regenerated my API key but the issue persists. Can you help?",
        "I can't login to my account since this morning. I've cleared cookies and tried incognito mode but nothing works.",
        "Would love to see a dark mode option. Our team works late hours and the bright interface is hard on our eyes.",
        "I was charged $348 this month but we only have 10 users. Can you explain the extra charges?",
        "Every time I try to upload a PDF to a task, I get an 'Upload failed' error. The file is only 5MB.",
        "How do I add a new team member to my project? I can't find the invite button.",
        "Our Slack integration stopped working yesterday. We're not getting any task notifications.",
        "The Gantt chart view is not loading properly. It shows a blank screen after the latest update.",
        "I've tried resetting my password 3 times but never receive the reset email. Checked spam too.",
        "I need to export all our project data for quarterly reporting. What format options are available?",
    ]

    @task(3)
    def submit_support_form(self):
        """Submit a support form."""
        idx = random.randint(0, len(self.subjects) - 1)
        payload = {
            "name": f"Load Test User {random.randint(1, 10000)}",
            "email": f"loadtest{random.randint(1, 10000)}@example.com",
            "subject": self.subjects[idx],
            "category": random.choice(self.categories),
            "message": self.messages[idx],
        }
        with self.client.post("/support/submit", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if "ticket_id" in data:
                    response.success()
                else:
                    response.failure("No ticket_id in response")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def check_ticket_status(self):
        """Check a ticket's status."""
        ticket_id = f"TKT-{random.randint(1, 1000)}"
        with self.client.get(f"/support/ticket/{ticket_id}", catch_response=True) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class EmailWebhookUser(HttpUser):
    """Simulate incoming Gmail webhook notifications."""
    wait_time = between(5, 20)
    weight = 2

    @task
    def gmail_webhook(self):
        """Simulate a Gmail Pub/Sub notification."""
        payload = {
            "message": {
                "data": "eyJlbWFpbEFkZHJlc3MiOiAidGVzdEBleGFtcGxlLmNvbSJ9",
                "messageId": f"gmail-msg-{random.randint(1, 100000)}",
            },
            "subscription": "projects/test/subscriptions/gmail-push",
        }
        with self.client.post("/webhooks/gmail", json=payload, catch_response=True) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class WhatsAppWebhookUser(HttpUser):
    """Simulate incoming WhatsApp messages via Twilio webhook."""
    wait_time = between(5, 15)
    weight = 2

    whatsapp_messages = [
        "how do i add a team member?",
        "help with password reset",
        "your app keeps crashing",
        "I need to talk to a human please",
        "how much does enterprise plan cost?",
        "can you explain how webhooks work?",
        "thanks for the help!",
        "is there a mobile app?",
        "the notifications are overwhelming",
        "agent",
    ]

    @task
    def whatsapp_webhook(self):
        """Simulate a Twilio WhatsApp webhook."""
        payload = {
            "MessageSid": f"SM{random.randint(10000000, 99999999)}",
            "From": f"whatsapp:+1{random.randint(2000000000, 9999999999)}",
            "Body": random.choice(self.whatsapp_messages),
            "ProfileName": f"Test User {random.randint(1, 1000)}",
        }
        with self.client.post(
            "/webhooks/whatsapp",
            data=payload,
            catch_response=True,
        ) as response:
            # 403 is expected without valid Twilio signature
            if response.status_code in [200, 202, 403]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class HealthCheckUser(HttpUser):
    """Monitor system health during load test."""
    wait_time = between(5, 15)
    weight = 1

    @task(2)
    def check_health(self):
        """Check system health endpoint."""
        self.client.get("/health")

    @task(1)
    def check_metrics(self):
        """Check metrics endpoint."""
        self.client.get("/metrics/channels")

    @task(1)
    def customer_lookup(self):
        """Lookup a customer by email."""
        email = f"loadtest{random.randint(1, 100)}@example.com"
        with self.client.get(
            "/customers/lookup",
            params={"email": email},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


# Event hooks for custom reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("=" * 60)
    print("Customer Success FTE - Load Test Started")
    print(f"Target host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("=" * 60)
    print("Customer Success FTE - Load Test Completed")
    print("=" * 60)
