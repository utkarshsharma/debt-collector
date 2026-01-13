"""Tests for factory classes."""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from factories import ClientFactory, DebtorFactory
from factories.debtor_factory import (
    PreDelinquencyDebtorFactory,
    EarlyDelinquencyDebtorFactory,
    LateDelinquencyDebtorFactory,
)
from schemas.enums import DelinquencyStage


class TestClientFactory:
    """Tests for ClientFactory."""

    def test_generates_valid_client(self):
        """Test that factory generates valid client data."""
        client = ClientFactory()

        assert isinstance(client["id"], UUID)
        assert "Test Finance Co" in client["name"]
        assert client["api_key"].startswith("test_key_")
        assert "example.com/webhook" in client["webhook_url"]
        assert client["is_active"] is True

    def test_generates_unique_clients(self):
        """Test that each client has unique values."""
        clients = ClientFactory.build_batch(5)

        ids = [c["id"] for c in clients]
        names = [c["name"] for c in clients]
        api_keys = [c["api_key"] for c in clients]

        assert len(set(ids)) == 5  # All unique IDs
        assert len(set(names)) == 5  # All unique names
        assert len(set(api_keys)) == 5  # All unique API keys


class TestDebtorFactory:
    """Tests for DebtorFactory."""

    def test_generates_valid_debtor(self):
        """Test that factory generates valid debtor data."""
        debtor = DebtorFactory()

        assert isinstance(debtor["id"], UUID)
        assert debtor["external_id"].startswith("TEST-LOAN-")
        assert debtor["phone"].startswith("+1555")
        assert len(debtor["phone"]) == 12  # +1555 + 7 digits
        assert "@test.example.com" in debtor["email"]
        assert isinstance(debtor["amount_owed"], Decimal)
        assert debtor["amount_owed"] > 0
        assert isinstance(debtor["stage"], DelinquencyStage)

    def test_phone_is_fake_555_number(self):
        """Test that all generated phones use 555 prefix."""
        debtors = DebtorFactory.build_batch(10)

        for debtor in debtors:
            assert debtor["phone"].startswith("+1555"), f"Phone should be 555 number: {debtor['phone']}"

    def test_names_are_clearly_fake(self):
        """Test that names are clearly fake test data."""
        debtors = DebtorFactory.build_batch(10)

        fake_surnames = ["Testuser", "Testaccount", "Testprofile", "Testdebtor"]
        for debtor in debtors:
            assert debtor["last_name"] in fake_surnames, f"Last name should be fake: {debtor['last_name']}"

    def test_external_id_has_test_prefix(self):
        """Test that external IDs have TEST- prefix."""
        debtors = DebtorFactory.build_batch(10)

        for debtor in debtors:
            assert debtor["external_id"].startswith("TEST-"), f"External ID should have TEST- prefix: {debtor['external_id']}"

    def test_generates_unique_debtors(self):
        """Test that each debtor has unique values."""
        debtors = DebtorFactory.build_batch(10)

        ids = [d["id"] for d in debtors]
        external_ids = [d["external_id"] for d in debtors]
        phones = [d["phone"] for d in debtors]

        assert len(set(ids)) == 10  # All unique IDs
        assert len(set(external_ids)) == 10  # All unique external IDs
        assert len(set(phones)) == 10  # All unique phones


class TestStageSpecificFactories:
    """Tests for stage-specific debtor factories."""

    def test_pre_delinquency_has_future_due_date(self):
        """Test pre-delinquency debtors have due dates in the future."""
        debtors = PreDelinquencyDebtorFactory.build_batch(10)

        today = date.today()
        for debtor in debtors:
            assert debtor["stage"] == DelinquencyStage.PRE_DELINQUENCY
            assert debtor["due_date"] > today, f"Due date should be in future: {debtor['due_date']}"

    def test_early_delinquency_has_recent_past_due_date(self):
        """Test early delinquency debtors have due dates 1-14 days ago."""
        debtors = EarlyDelinquencyDebtorFactory.build_batch(10)

        today = date.today()
        for debtor in debtors:
            assert debtor["stage"] == DelinquencyStage.EARLY_DELINQUENCY
            assert debtor["due_date"] < today, f"Due date should be in past: {debtor['due_date']}"
            days_overdue = (today - debtor["due_date"]).days
            assert 1 <= days_overdue <= 14, f"Should be 1-14 days overdue: {days_overdue}"

    def test_late_delinquency_has_old_due_date(self):
        """Test late delinquency debtors have due dates 21+ days ago."""
        debtors = LateDelinquencyDebtorFactory.build_batch(10)

        today = date.today()
        for debtor in debtors:
            assert debtor["stage"] == DelinquencyStage.LATE_DELINQUENCY
            assert debtor["due_date"] < today, f"Due date should be in past: {debtor['due_date']}"
            days_overdue = (today - debtor["due_date"]).days
            assert days_overdue >= 21, f"Should be 21+ days overdue: {days_overdue}"
