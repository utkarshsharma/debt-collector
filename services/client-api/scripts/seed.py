#!/usr/bin/env python3
"""Seed the database with test data."""

import asyncio
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent dir to path (so 'src' is a package)
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.config import get_settings
from src.core.database import Base
from src.models import Client, Debtor, Call, PaymentPromise, SMSLog

settings = get_settings()


async def seed_database():
    """Seed the database with test data."""
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Tables created")

    async with async_session() as session:
        # Check if we already have data
        result = await session.execute(text("SELECT COUNT(*) FROM clients"))
        count = result.scalar()
        if count > 0:
            print("Database already has data. Skipping seed.")
            return

        # Create demo client
        client = Client(
            id=uuid4(),
            name="Demo Finance Company",
            api_key="demo_api_key_12345",
            webhook_url="https://example.com/webhook",
            is_active=True,
        )
        session.add(client)
        await session.flush()
        print(f"✓ Created client: {client.name}")

        # Test debtors data
        debtors_data = [
            {
                "first_name": "Utkarsh",
                "last_name": "Sharma",
                "phone": "+31619436953",
                "email": "utkarsh@example.com",
                "amount_owed": Decimal("2450.00"),
                "due_date": (datetime.now() - timedelta(days=15)).date(),
                "stage": "early_delinquency",
                "metadata_": {"original_creditor": "CreditMax Bank", "account_number": "ACC-001234"},
            },
            {
                "first_name": "Abhishek",
                "last_name": "Loiwal",
                "phone": "+31612345678",
                "email": "abhishek@example.com",
                "amount_owed": Decimal("1875.50"),
                "due_date": (datetime.now() - timedelta(days=5)).date(),
                "stage": "pre_delinquency",
                "metadata_": {"original_creditor": "FirstChoice Finance", "account_number": "ACC-005678"},
            },
            {
                "first_name": "Shreyan",
                "last_name": "Sahukar",
                "phone": "+31698765432",
                "email": "shreyan@example.com",
                "amount_owed": Decimal("3200.00"),
                "due_date": (datetime.now() - timedelta(days=45)).date(),
                "stage": "late_delinquency",
                "metadata_": {"original_creditor": "QuickLoans Inc", "account_number": "ACC-009012"},
            },
            {
                "first_name": "Harsh",
                "last_name": "Sharma",
                "phone": "+31687654321",
                "email": "harsh@example.com",
                "amount_owed": Decimal("950.25"),
                "due_date": (datetime.now() - timedelta(days=10)).date(),
                "stage": "early_delinquency",
                "metadata_": {"original_creditor": "PayDay Express", "account_number": "ACC-003456"},
            },
        ]

        debtors = []
        for data in debtors_data:
            debtor = Debtor(
                id=uuid4(),
                client_id=client.id,
                **data,
            )
            session.add(debtor)
            debtors.append(debtor)
            print(f"✓ Created debtor: {debtor.first_name} {debtor.last_name}")

        await session.flush()

        # Add some sample calls for the first debtor (Utkarsh)
        utkarsh = debtors[0]

        # Completed call with payment promise
        call1 = Call(
            id=uuid4(),
            debtor_id=utkarsh.id,
            client_id=client.id,
            status="completed",
            outcome="payment_promise",
            final_state="commitment",
            initiated_at=datetime.now() - timedelta(days=2),
            started_at=datetime.now() - timedelta(days=2),
            answered_at=datetime.now() - timedelta(days=2),
            ended_at=datetime.now() - timedelta(days=2) + timedelta(minutes=5),
            duration_sec=300,
            from_number="+3197010225408",
            to_number=utkarsh.phone,
            transcript="Agent: Hello, am I speaking with Utkarsh Sharma?\nDebtor: Yes, this is Utkarsh.\nAgent: I'm calling regarding your outstanding balance of $2,450 with CreditMax Bank. Are you able to discuss payment options today?\nDebtor: Yes, I've been meaning to pay. I can pay $500 next week.\nAgent: That's great to hear. Can you confirm the date you'll make this payment?\nDebtor: Friday, the 24th.\nAgent: Perfect. I'll send you a confirmation SMS with the payment details.",
            extraction={
                "outcome": "payment_promise",
                "verified_identity": True,
                "payment_promise": {"amount": 500, "date": (datetime.now() + timedelta(days=7)).isoformat()},
                "sentiment": "cooperative",
                "summary": "Debtor confirmed identity and agreed to pay $500 on Friday. Positive interaction.",
            },
            sentiment_score=Decimal("0.85"),
        )
        session.add(call1)

        # Add payment promise
        promise = PaymentPromise(
            id=uuid4(),
            call_id=call1.id,
            debtor_id=utkarsh.id,
            amount=Decimal("500.00"),
            promise_date=(datetime.now() + timedelta(days=7)).date(),
            status="pending",
        )
        session.add(promise)

        # Add SMS for that call
        sms = SMSLog(
            id=uuid4(),
            call_id=call1.id,
            debtor_id=utkarsh.id,
            from_phone="+3197010225408",
            to_phone=utkarsh.phone,
            message="Hi Utkarsh, this confirms your payment commitment of $500 due on Friday. Thank you for your cooperation. - VoiceCollect",
            status="delivered",
            sms_type="payment_confirmation",
        )
        session.add(sms)
        print(f"✓ Created call with payment promise for {utkarsh.first_name} {utkarsh.last_name}")

        # Add a call for Shreyan (late delinquency - dispute)
        shreyan = debtors[2]
        call2 = Call(
            id=uuid4(),
            debtor_id=shreyan.id,
            client_id=client.id,
            status="completed",
            outcome="dispute",
            final_state="objection",
            initiated_at=datetime.now() - timedelta(days=1),
            started_at=datetime.now() - timedelta(days=1),
            answered_at=datetime.now() - timedelta(days=1),
            ended_at=datetime.now() - timedelta(days=1) + timedelta(minutes=8),
            duration_sec=480,
            from_number="+3197010225408",
            to_number=shreyan.phone,
            transcript="Agent: Hello, is this Shreyan Sahukar?\nDebtor: Yes, who is this?\nAgent: I'm calling from VoiceCollect regarding your balance of $3,200 with QuickLoans Inc.\nDebtor: I already told you people, I dispute this debt. I never took out this loan.\nAgent: I understand. Would you like me to send you documentation to verify the debt?\nDebtor: Yes, send me everything. I'm not paying anything until I see proof.",
            extraction={
                "outcome": "dispute",
                "verified_identity": True,
                "sentiment": "hostile",
                "summary": "Debtor disputes the debt and requests verification documentation. Escalate to disputes team.",
                "next_steps": "Send debt verification letter. Flag for disputes team review.",
            },
            sentiment_score=Decimal("0.25"),
        )
        session.add(call2)
        print(f"✓ Created dispute call for {shreyan.first_name} {shreyan.last_name}")

        await session.commit()
        print("\n✅ Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
