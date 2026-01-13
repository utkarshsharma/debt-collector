"""Factory for generating mock client (finance company) data."""

import factory
from uuid import uuid4
from datetime import datetime


class ClientFactory(factory.Factory):
    """
    Factory for generating mock finance company clients.

    Usage:
        client = ClientFactory()  # Single client
        clients = ClientFactory.build_batch(5)  # Multiple clients
    """

    class Meta:
        model = dict

    id = factory.LazyFunction(uuid4)
    name = factory.Sequence(lambda n: f"Test Finance Co {n + 1}")
    api_key = factory.LazyFunction(lambda: f"test_key_{uuid4().hex[:16]}")
    webhook_url = factory.Sequence(lambda n: f"https://test-client-{n + 1}.example.com/webhook")
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class RealClientFactory(ClientFactory):
    """
    Factory for your real test client profile.
    Override with your actual company details for E2E testing.
    """

    name = "My Test Company"
    webhook_url = "https://webhook.site/your-unique-url"  # Replace with real webhook for testing
