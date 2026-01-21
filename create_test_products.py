#!/usr/bin/env python3
"""Create test products accessible to the test-token principal."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.database.database_session import get_db_session
from src.core.database.models import Product, Principal
from datetime import datetime, UTC
from sqlalchemy import select


def create_test_products():
    """Create test products that are accessible to test-token principal."""
    with get_db_session() as session:
        # Get the test principal
        principal_stmt = select(Principal).filter_by(
            tenant_id="default",
            access_token="test-token"
        )
        principal = session.scalars(principal_stmt).first()
        
        if not principal:
            print("❌ Test principal not found. Run create_test_principal.py first.")
            return
        
        principal_id = principal.principal_id
        print(f"✅ Found principal: {principal_id}")
        
        # Check if products already exist
        existing_products = session.scalars(
            select(Product).filter_by(tenant_id="default")
        ).all()
        
        if existing_products:
            print(f"\n📦 Found {len(existing_products)} existing products")
            # Update existing products to be accessible (remove restrictions)
            updated_count = 0
            for product in existing_products:
                if product.allowed_principal_ids:
                    print(f"   Updating {product.product_id}: removing access restrictions")
                    product.allowed_principal_ids = None  # Make accessible to all
                    updated_count += 1
                else:
                    print(f"   {product.product_id}: already accessible")
            
            if updated_count > 0:
                session.commit()
                print(f"✅ Updated {updated_count} products to be accessible")
        else:
            print("\n📦 No products found. Creating test products...")
            
            # Create TF1-specific products
            products = [
                Product(
                    tenant_id="default",
                    product_id="prod_tf1_prime_time",
                    name="Prime Time TF1",
                    description="Espaces publicitaires en prime time (20h-22h) sur TF1",
                    format_ids=[
                        {"agent_url": "https://creative.adcontextprotocol.org", "id": "display_300x250"},
                        {"agent_url": "https://creative.adcontextprotocol.org", "id": "display_728x90"},
                    ],
                    targeting_template={"time_slot": "prime_time", "channel": "TF1"},
                    delivery_type="guaranteed",
                    delivery_measurement={"provider": "MediaMetrie"},
                    price_guidance={"floor": 50.0, "p50": 75.0, "p75": 100.0},
                    property_tags=["all_inventory"],
                    allowed_principal_ids=None,  # Accessible to all
                    created_at=datetime.now(UTC),
                ),
                Product(
                    tenant_id="default",
                    product_id="prod_tf1_sport",
                    name="Sport TF1",
                    description="Espaces publicitaires sur les programmes sport de TF1",
                    format_ids=[
                        {"agent_url": "https://creative.adcontextprotocol.org", "id": "display_300x250"},
                        {"agent_url": "https://creative.adcontextprotocol.org", "id": "video_standard", "duration_ms": 30000},
                    ],
                    targeting_template={"content_type": "sport", "channel": "TF1"},
                    delivery_type="guaranteed",
                    delivery_measurement={"provider": "MediaMetrie"},
                    price_guidance={"floor": 40.0, "p50": 60.0, "p75": 80.0},
                    property_tags=["all_inventory"],
                    allowed_principal_ids=None,  # Accessible to all
                    created_at=datetime.now(UTC),
                ),
                Product(
                    tenant_id="default",
                    product_id="prod_tf1_jt",
                    name="Journal Télévisé TF1",
                    description="Espaces publicitaires pendant le Journal Télévisé de TF1",
                    format_ids=[
                        {"agent_url": "https://creative.adcontextprotocol.org", "id": "display_300x250"},
                    ],
                    targeting_template={"content_type": "news", "channel": "TF1"},
                    delivery_type="guaranteed",
                    delivery_measurement={"provider": "MediaMetrie"},
                    price_guidance={"floor": 45.0, "p50": 65.0, "p75": 85.0},
                    property_tags=["all_inventory"],
                    allowed_principal_ids=None,  # Accessible to all
                    created_at=datetime.now(UTC),
                ),
            ]
            
            for product in products:
                session.add(product)
            
            session.commit()
            print(f"✅ Created {len(products)} test products:")
            for product in products:
                print(f"   - {product.name} ({product.product_id})")
        
        # Verify products are accessible
        accessible_products = session.scalars(
            select(Product).filter_by(tenant_id="default")
        ).all()
        
        print(f"\n✅ Total products accessible to test-token: {len(accessible_products)}")
        for product in accessible_products:
            access_info = "all principals" if not product.allowed_principal_ids else f"restricted to {product.allowed_principal_ids}"
            print(f"   - {product.name}: {access_info}")


if __name__ == "__main__":
    create_test_products()
