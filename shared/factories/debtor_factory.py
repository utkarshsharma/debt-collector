"""Factory for generating mock debtor data."""

import factory
from uuid import uuid4
from datetime import date, datetime, timedelta
from decimal import Decimal
import random

from schemas.enums import DelinquencyStage


# Mock first names for test data
FIRST_NAMES = ["John", "Jane", "Mike", "Sarah", "David", "Emily", "Chris", "Lisa", "Tom", "Amy"]

# Mock last names (all end with "Testuser" to be clearly fake)
LAST_NAMES = ["Testuser", "Testaccount", "Testprofile", "Testdebtor"]


class DebtorFactory(factory.Factory):
    """
    Factory for generating mock debtor data.

    Follows conventions:
    - Phone: +1555XXXXXXX (fake 555 numbers)
    - Names: Clearly fake (e.g., "John Testuser")
    - External IDs: TEST- prefix
    - Emails: @test.example.com

    Usage:
        debtor = DebtorFactory()  # Single debtor
        debtors = DebtorFactory.build_batch(10)  # Multiple debtors
        pre_del = DebtorFactory(stage=DelinquencyStage.PRE_DELINQUENCY)
    """

    class Meta:
        model = dict

    # IDs
    id = factory.LazyFunction(uuid4)
    client_id = factory.LazyFunction(uuid4)
    external_id = factory.Sequence(lambda n: f"TEST-LOAN-{n + 1:04d}")

    # Personal info (clearly fake)
    first_name = factory.LazyFunction(lambda: random.choice(FIRST_NAMES))
    last_name = factory.LazyFunction(lambda: random.choice(LAST_NAMES))

    # Phone: +1555 + 7 random digits (555 is reserved for fake numbers)
    phone = factory.LazyFunction(
        lambda: f"+1555{random.randint(1000000, 9999999)}"
    )

    # Email: firstname.lastname@test.example.com
    email = factory.LazyAttribute(
        lambda o: f"{o.first_name.lower()}.{o.last_name.lower()}@test.example.com"
    )

    # Location
    timezone = "America/New_York"

    # Debt details
    amount_owed = factory.LazyFunction(
        lambda: Decimal(str(random.choice([500, 1000, 1500, 2000, 2500, 5000])))
    )
    currency = "USD"

    # Due date: random within -30 to +30 days from today
    due_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=random.randint(-30, 30))
    )

    # Stage: random by default
    stage = factory.LazyFunction(
        lambda: random.choice(list(DelinquencyStage))
    )

    # Metadata
    metadata = None
    opted_out = False
    opted_out_at = None

    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class PreDelinquencyDebtorFactory(DebtorFactory):
    """Debtor with payment due in the future (pre-delinquency stage)."""

    stage = DelinquencyStage.PRE_DELINQUENCY
    due_date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=random.randint(3, 7))
    )


class EarlyDelinquencyDebtorFactory(DebtorFactory):
    """Debtor ~1 week past due (early delinquency stage)."""

    stage = DelinquencyStage.EARLY_DELINQUENCY
    due_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=random.randint(1, 14))
    )


class LateDelinquencyDebtorFactory(DebtorFactory):
    """Debtor 3+ weeks past due (late delinquency stage)."""

    stage = DelinquencyStage.LATE_DELINQUENCY
    due_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=random.randint(21, 60))
    )


class RealDebtorFactory(DebtorFactory):
    """
    Factory for your real test profile for E2E testing.

    Override these values with your actual details:
        debtor = RealDebtorFactory(
            phone="+1YOUR_PHONE",
            first_name="YourName",
            last_name="YourLastName"
        )
    """

    external_id = "E2E-TEST-001"
    first_name = "Test"  # Replace with your name
    last_name = "User"   # Replace with your name
    phone = "+15551234567"  # Replace with your real phone for E2E
    email = "test@example.com"  # Replace with your email
    amount_owed = Decimal("1500.00")
    stage = DelinquencyStage.PRE_DELINQUENCY
