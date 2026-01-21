#!/usr/bin/env python3
"""Create a test principal with access token."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.database.database_session import get_db_session
from src.core.database.models import Principal
from datetime import datetime, UTC


def create_test_principal():
    """Create a test principal with access token."""
    with get_db_session() as session:
        # Check if principal already exists
        existing = session.query(Principal).filter_by(
            tenant_id="default",
            principal_id="test_principal"
        ).first()
        
        if existing:
            print(f"✅ Principal already exists:")
            print(f"   Name: {existing.name}")
            print(f"   Token: {existing.access_token}")
            return existing.access_token
        
        # Create new principal
        principal = Principal(
            tenant_id="default",
            principal_id="test_principal",
            name="Test Advertiser",
            access_token="test-token",
            platform_mappings={
                "mock": {"advertiser_id": "test_advertiser"}
            },
            created_at=datetime.now(UTC),
        )
        
        session.add(principal)
        session.commit()
        
        print(f"✅ Created test principal:")
        print(f"   Name: {principal.name}")
        print(f"   Token: {principal.access_token}")
        return principal.access_token


if __name__ == "__main__":
    token = create_test_principal()
    print(f"\n💡 Use this token for testing:")
    print(f'   export TOKEN="{token}"')
