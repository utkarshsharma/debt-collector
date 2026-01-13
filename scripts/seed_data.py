#!/usr/bin/env python3
"""
Seed script for generating test data.

Usage:
    python scripts/seed_data.py              # Generate 15 mock debtors
    python scripts/seed_data.py --count 20   # Generate 20 mock debtors
    python scripts/seed_data.py --e2e        # Include your real E2E test profile

This script generates mock data for testing. Once the database is set up,
it will insert data into PostgreSQL.
"""

import argparse
import sys
from pathlib import Path

# Add shared package to path
shared_path = Path(__file__).parent.parent / "shared"
sys.path.insert(0, str(shared_path))

from factories import ClientFactory, DebtorFactory
from factories.debtor_factory import (
    PreDelinquencyDebtorFactory,
    EarlyDelinquencyDebtorFactory,
    LateDelinquencyDebtorFactory,
    RealDebtorFactory,
)
from factories.client_factory import RealClientFactory


# =============================================================================
# E2E TEST PROFILE - Replace with your real details for end-to-end testing
# =============================================================================
E2E_CONFIG = {
    "phone": "+15551234567",      # TODO: Replace with your real phone number
    "first_name": "Utkarsh",      # TODO: Replace with your first name
    "last_name": "Sharma",        # TODO: Replace with your last name
    "email": "test@example.com",  # TODO: Replace with your email
    "amount_owed": "1500.00",     # Test debt amount
}
# =============================================================================


def generate_mock_data(count: int = 15, include_e2e: bool = False):
    """
    Generate mock test data.

    Args:
        count: Number of mock debtors to generate
        include_e2e: Whether to include your real E2E test profile
    """
    print("=" * 60)
    print("DEBT COLLECTOR - TEST DATA GENERATOR")
    print("=" * 60)

    # Generate a test client (finance company)
    client = ClientFactory()
    print(f"\n📋 TEST CLIENT (Finance Company)")
    print(f"   Name: {client['name']}")
    print(f"   API Key: {client['api_key']}")
    print(f"   Webhook: {client['webhook_url']}")

    # Generate debtors with distribution across stages
    pre_del_count = count // 3
    early_del_count = count // 3
    late_del_count = count - pre_del_count - early_del_count

    print(f"\n📊 GENERATING {count} MOCK DEBTORS")
    print(f"   Pre-delinquency: {pre_del_count}")
    print(f"   Early delinquency: {early_del_count}")
    print(f"   Late delinquency: {late_del_count}")

    debtors = []

    # Pre-delinquency (payment due soon)
    for debtor in PreDelinquencyDebtorFactory.build_batch(pre_del_count):
        debtor["client_id"] = client["id"]
        debtors.append(debtor)

    # Early delinquency (~1 week past due)
    for debtor in EarlyDelinquencyDebtorFactory.build_batch(early_del_count):
        debtor["client_id"] = client["id"]
        debtors.append(debtor)

    # Late delinquency (3+ weeks past due)
    for debtor in LateDelinquencyDebtorFactory.build_batch(late_del_count):
        debtor["client_id"] = client["id"]
        debtors.append(debtor)

    # Print sample debtors
    print(f"\n📝 SAMPLE DEBTORS (showing first 5):")
    print("-" * 60)
    for i, debtor in enumerate(debtors[:5]):
        print(f"\n   Debtor {i + 1}:")
        print(f"   Name: {debtor['first_name']} {debtor['last_name']}")
        print(f"   Phone: {debtor['phone']}")
        print(f"   Amount: ${debtor['amount_owed']}")
        print(f"   Due: {debtor['due_date']}")
        print(f"   Stage: {debtor['stage'].value}")

    # E2E test profile
    if include_e2e:
        print(f"\n🎯 E2E TEST PROFILE (for real call testing)")
        print("-" * 60)

        if E2E_CONFIG["phone"] == "+15551234567":
            print("   ⚠️  WARNING: E2E profile still has placeholder phone!")
            print("   Edit scripts/seed_data.py and update E2E_CONFIG")
            print("   with your real phone number to receive test calls.")
        else:
            from decimal import Decimal
            e2e_debtor = RealDebtorFactory(
                client_id=client["id"],
                phone=E2E_CONFIG["phone"],
                first_name=E2E_CONFIG["first_name"],
                last_name=E2E_CONFIG["last_name"],
                email=E2E_CONFIG["email"],
                amount_owed=Decimal(E2E_CONFIG["amount_owed"]),
            )
            debtors.append(e2e_debtor)
            print(f"   Name: {e2e_debtor['first_name']} {e2e_debtor['last_name']}")
            print(f"   Phone: {e2e_debtor['phone']}")
            print(f"   Amount: ${e2e_debtor['amount_owed']}")
            print(f"   Stage: {e2e_debtor['stage'].value}")

    print(f"\n✅ Generated {len(debtors)} debtors total")
    print("=" * 60)

    return {
        "client": client,
        "debtors": debtors,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate test data for debt collector")
    parser.add_argument(
        "--count",
        type=int,
        default=15,
        help="Number of mock debtors to generate (default: 15)",
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="Include your real E2E test profile",
    )
    args = parser.parse_args()

    data = generate_mock_data(count=args.count, include_e2e=args.e2e)

    # TODO: Once database is set up, insert data here
    # from database import SessionLocal
    # db = SessionLocal()
    # for debtor in data["debtors"]:
    #     db.add(Debtor(**debtor))
    # db.commit()

    print("\n💡 Note: Data generated in memory only.")
    print("   Once Client API service is built, this will insert into PostgreSQL.")


if __name__ == "__main__":
    main()
