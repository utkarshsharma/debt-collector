#!/usr/bin/env python3
"""Test Supabase database connection.

Usage:
    cd services/client-api
    python scripts/test_supabase_connection.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent.parent / ".env")


async def test_connection():
    """Test database connection and verify tables."""
    from sqlalchemy import text

    from core.config import get_settings
    from core.database import engine, verify_database_connection

    settings = get_settings()

    print("=" * 60)
    print("Supabase Connection Test")
    print("=" * 60)

    # Mask password in URL for display
    url = settings.database_url
    if "@" in url:
        # Hide password: postgresql+asyncpg://user:PASS@host -> postgresql+asyncpg://user:***@host
        prefix, rest = url.split("://", 1)
        if ":" in rest and "@" in rest:
            user_pass, host = rest.split("@", 1)
            user = user_pass.split(":")[0]
            url = f"{prefix}://{user}:***@{host}"
    print(f"\nDatabase URL: {url}")

    # Test 1: Basic connection
    print("\n[1/4] Testing basic connection...")
    try:
        await verify_database_connection()
        print("  ✓ Connection successful")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False

    # Test 2: Check database version
    print("\n[2/4] Checking database version...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"  ✓ PostgreSQL version: {version[:50]}...")
    except Exception as e:
        print(f"  ✗ Failed to get version: {e}")

    # Test 3: List tables
    print("\n[3/4] Listing tables...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            if tables:
                print(f"  ✓ Found {len(tables)} tables:")
                for table in tables:
                    print(f"    - {table}")
            else:
                print("  ⚠ No tables found (run migrations first)")
    except Exception as e:
        print(f"  ✗ Failed to list tables: {e}")

    # Test 4: Check expected tables
    print("\n[4/4] Checking expected model tables...")
    expected_tables = {"clients", "debtors", "calls", "payment_promises", "sms_logs"}
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
            )
            existing = {row[0] for row in result.fetchall()}
            missing = expected_tables - existing
            if missing:
                print(f"  ⚠ Missing tables (run migrations): {', '.join(missing)}")
            else:
                print("  ✓ All expected tables exist")
    except Exception as e:
        print(f"  ✗ Failed to check tables: {e}")

    print("\n" + "=" * 60)
    print("Connection test completed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
